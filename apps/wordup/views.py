import os
import base64
import tempfile
import logging
from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import google.generativeai as genai

from .models import Word, UserWordProgress
from .serializers import (
    WordSerializer,
    UserWordProgressSerializer,
    EvaluateExampleRequest,
    EvaluateExampleResponse,
    MasterWordRequest,
)
from apps.ai_evaluation.services import WhisperService
from apps.gamification.models import PointsTransaction

logger = logging.getLogger(__name__)


class GetRandomWordView(APIView):
    """
    GET /api/v1/wordup/random-word/
    Returns a random word for the user to practice.
    Prioritizes words not yet mastered.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get words not yet mastered by user
        mastered_word_ids = UserWordProgress.objects.filter(
            user=user,
            is_mastered=True
        ).values_list('word_id', flat=True)
        
        # Get a random word not yet mastered
        available_words = Word.objects.exclude(id__in=mastered_word_ids)
        
        # If all words are mastered, get any word
        if not available_words.exists():
            available_words = Word.objects.all()
        
        word = available_words.order_by('?').first()
        
        if not word:
            return Response(
                {"error": "No words available"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create progress for this word
        progress, created = UserWordProgress.objects.get_or_create(
            user=user,
            word=word
        )
        
        serializer = WordSerializer(word)
        return Response({
            'word': serializer.data,
            'progress': UserWordProgressSerializer(progress).data
        })


class EvaluateExampleView(APIView):
    """
    POST /api/v1/wordup/evaluate/
    Evaluates user's example sentence using Gemini.
    Supports both text input and audio transcription.
    """
    permission_classes = [IsAuthenticated]
    
    async def _transcribe_audio(self, audio_base64: str) -> str:
        """Transcribe audio using Whisper."""
        try:
            audio_bytes = base64.b64decode(audio_base64)
            whisper_service = WhisperService()
            
            result = await whisper_service.transcribe_audio(
                audio_bytes,
                prefer_faster_whisper=True
            )
            
            return result.get('text', '').strip()
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            raise
    
    def _evaluate_with_gemini(self, word: str, definition: str, example_sentence: str) -> dict:
        """Use Gemini to evaluate if the example sentence is acceptable."""
        # Get API key from multiple sources (same pattern as GrammarPractice)
        from django.conf import settings
        api_key = (
            getattr(settings, 'GEMINI_API_KEY', '') or 
            os.environ.get('GEMINI_API_KEY', '') or 
            os.environ.get('GOOGLE_API_KEY', '')
        )
        
        if not api_key:
            logger.error("GEMINI_API_KEY not configured")
            return {
                'is_acceptable': False,
                'feedback': 'Unable to evaluate. Please contact support (API key missing).'
            }
        
        # Try multiple Gemini models with fallback (same pattern as GrammarPractice)
        genai.configure(api_key=api_key)
        
        candidates = [
            getattr(settings, 'GEMINI_TEXT_MODEL', None) or os.environ.get('GEMINI_MODEL') or 'gemini-2.5-flash',
            'gemini-2.5-pro',
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro',
        ]
        
        prompt = f"""You are an English language tutor evaluating a student's example sentence.

Word: {word}
Definition: {definition}

Student's example sentence: "{example_sentence}"

Evaluate if this sentence:
1. Uses the word "{word}" correctly
2. Demonstrates understanding of the word's meaning
3. Is grammatically acceptable (minor errors are OK)
4. Makes logical sense

Respond in JSON format:
{{
    "is_acceptable": true/false,
    "feedback": "Brief, encouraging feedback (2-3 sentences). If acceptable, praise them. If not, explain what's wrong and give a hint."
}}

Be encouraging and supportive. Focus on whether they understand the word, not perfect grammar.
"""
        
        # Try each model candidate
        import json
        for model_name in candidates:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                text = getattr(response, 'text', None)
                
                if not text:
                    continue
                
                text = text.strip()
                
                # Parse JSON from response
                if text.startswith('```json'):
                    text = text.split('```json')[1].split('```')[0].strip()
                elif text.startswith('```'):
                    text = text.split('```')[1].split('```')[0].strip()
                
                result = json.loads(text)
                
                return {
                    'is_acceptable': result.get('is_acceptable', False),
                    'feedback': result.get('feedback', 'Unable to evaluate. Please try again.')
                }
                
            except Exception as e:
                logger.warning(f"Gemini evaluation via {model_name} failed: {e}")
                continue
        
        # All models failed
        logger.error("All Gemini models failed for WordUp evaluation")
        return {
            'is_acceptable': False,
            'feedback': 'Unable to evaluate your sentence. Please try again later.'
        }
    
    def post(self, request):
        serializer = EvaluateExampleRequest(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        word_id = data['word_id']
        example_sentence = data.get('example_sentence', '').strip()
        audio_base64 = data.get('audio_base64', '')
        
        # Get the word
        try:
            word = Word.objects.get(id=word_id)
        except Word.DoesNotExist:
            return Response(
                {"error": "Word not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Transcribe audio if provided
        if audio_base64 and not example_sentence:
            try:
                import asyncio
                example_sentence = asyncio.run(self._transcribe_audio(audio_base64))
            except Exception as e:
                return Response(
                    {"error": f"Failed to transcribe audio: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not example_sentence:
            return Response(
                {"error": "Example sentence is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create progress
        progress, _ = UserWordProgress.objects.get_or_create(
            user=request.user,
            word=word
        )
        
        # Increment attempts
        progress.attempts += 1
        
        # Evaluate with Gemini
        evaluation = self._evaluate_with_gemini(
            word.word,
            word.definition,
            example_sentence
        )
        
        is_acceptable = evaluation['is_acceptable']
        feedback = evaluation['feedback']
        
        # If acceptable, mark as mastered and award XP
        if is_acceptable and not progress.is_mastered:
            progress.is_mastered = True
            progress.mastered_at = timezone.now()
            progress.user_example_sentence = example_sentence
            
            # Award XP based on difficulty
            xp_rewards = {
                'beginner': 10,
                'intermediate': 20,
                'advanced': 30,
            }
            xp = xp_rewards.get(word.difficulty, 10)
            
            try:
                PointsTransaction.objects.create(
                    user=request.user,
                    amount=xp,
                    source='wordup_mastery',
                    context={'word_id': word.id, 'word': word.word, 'difficulty': word.difficulty}
                )
            except Exception as e:
                logger.error(f"Failed to award XP: {e}")
        
        progress.save()
        
        response_serializer = EvaluateExampleResponse(data={
            'is_acceptable': is_acceptable,
            'feedback': feedback,
            'word_id': word.id,
            'is_mastered': progress.is_mastered,
        })
        response_serializer.is_valid(raise_exception=True)
        
        return Response(response_serializer.data)


class MasteredWordsView(APIView):
    """
    GET /api/v1/wordup/mastered-words/
    Returns list of words mastered by the user.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        mastered = UserWordProgress.objects.filter(
            user=user,
            is_mastered=True
        ).select_related('word').order_by('-mastered_at')
        
        serializer = UserWordProgressSerializer(mastered, many=True)
        
        return Response({
            'mastered_words': serializer.data,
            'total_mastered': mastered.count()
        })


class WordProgressStatsView(APIView):
    """
    GET /api/v1/wordup/stats/
    Returns user's WordUp statistics.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        total_words = Word.objects.count()
        mastered_count = UserWordProgress.objects.filter(
            user=user,
            is_mastered=True
        ).count()
        in_progress_count = UserWordProgress.objects.filter(
            user=user,
            is_mastered=False
        ).count()
        
        return Response({
            'total_words': total_words,
            'mastered_count': mastered_count,
            'in_progress_count': in_progress_count,
            'completion_percentage': round((mastered_count / total_words * 100) if total_words > 0 else 0, 2)
        })
