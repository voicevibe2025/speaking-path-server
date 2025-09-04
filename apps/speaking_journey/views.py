import re
import string
import tempfile
import os
import base64
import io
import wave
import uuid
import logging
import hashlib
from difflib import SequenceMatcher
import whisper
import google.generativeai as genai
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
import requests
from .models import Topic, TopicProgress, UserProfile, PhraseProgress, UserPhraseRecording
from apps.gamification.models import UserLevel
from .serializers import (
    SpeakingTopicsResponseSerializer,
    SpeakingTopicDtoSerializer,
    CompleteTopicResponseSerializer,
    UserProfileSerializer,
    PhraseProgressSerializer,
    PhraseSubmissionResultSerializer,
    UserPhraseRecordingSerializer,
    UserPhraseRecordingsResponseSerializer,
)

logger = logging.getLogger(__name__)

def _compute_unlocks(user):
    topics = list(Topic.objects.filter(is_active=True).order_by('sequence'))
    completed_sequences = set(
        TopicProgress.objects.filter(user=user, completed=True, topic__is_active=True)
        .values_list('topic__sequence', flat=True)
    )
    unlocked_sequences = set()
    if topics:
        unlocked_sequences.add(topics[0].sequence)
    for t in topics:
        if t.sequence in completed_sequences:
            unlocked_sequences.add(t.sequence)
        else:
            # Unlock if previous is completed
            prev_seq = t.sequence - 1
            if prev_seq in completed_sequences:
                unlocked_sequences.add(t.sequence)
    return topics, completed_sequences, unlocked_sequences


def _normalize_text(text):
    """Normalize text for comparison: lowercase, remove punctuation, extra spaces"""
    if not text:
        return ""
    # Convert to lowercase and remove punctuation
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Remove extra whitespaces and normalize
    text = ' '.join(text.split())
    return text


def _calculate_similarity(expected, actual):
    """Calculate text similarity percentage (0-100)"""
    expected_norm = _normalize_text(expected)
    actual_norm = _normalize_text(actual)

    if not expected_norm or not actual_norm:
        return 0.0

    # Use SequenceMatcher for similarity calculation
    similarity = SequenceMatcher(None, expected_norm, actual_norm).ratio()
    return similarity * 100


def _get_gemini_feedback(expected_phrase, transcribed_text, accuracy):
    """Get pronunciation feedback from Gemini AI"""
    try:
        # Configure Gemini (make sure GEMINI_API_KEY is in settings)
        genai.configure(api_key=getattr(settings, 'GEMINI_API_KEY', ''))
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        You are a pronunciation tutor. A student tried to say: "{expected_phrase}"
        But the speech recognition heard: "{transcribed_text}"
        The accuracy was {accuracy:.1f}%.

        Please provide brief, encouraging feedback (2-3 sentences max) focusing on:
        - What they did well (if accuracy > 60%)
        - Specific pronunciation tips for improvement
        - Keep it positive and motivating

        Example good feedback: "Good effort! Your pronunciation of 'Hello' was clear. Try to speak a bit slower and emphasize the ending of 'name' more clearly."
        """

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        # Fallback feedback if Gemini fails
        if accuracy >= 80:
            return "Great job! Your pronunciation was excellent."
        elif accuracy >= 60:
            return "Good effort! Try speaking a bit more clearly and slowly."
        else:
            return "Keep practicing! Focus on pronouncing each word clearly."


def _transcribe_audio_with_whisper(audio_file):
    """Transcribe audio using OpenAI Whisper tiny.en model"""
    try:
        # Load Whisper model (tiny.en for faster processing on your MX350)
        model = whisper.load_model("tiny.en")

        # Create temporary file for audio processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            # Write uploaded audio to temporary file
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            # Transcribe audio
            result = model.transcribe(temp_file_path)
            transcription = result.get("text", "").strip()
            return transcription
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return ""


class SpeakingTopicsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        topics, completed_sequences, unlocked_sequences = _compute_unlocks(request.user)

        # Get or create user profile for welcome screen personalization
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'first_visit': True}
        )

        # Fetch all phrase progress for this user
        phrase_progress_dict = {}
        for topic in topics:
            phrase_progress, _ = PhraseProgress.objects.get_or_create(
                user=request.user,
                topic=topic,
                defaults={'current_phrase_index': 0, 'completed_phrases': []}
            )
            phrase_progress_dict[topic.id] = phrase_progress

        payload = []
        for t in topics:
            # Get phrase progress for this topic
            phrase_prog = phrase_progress_dict.get(t.id)
            phrase_progress_data = None
            if phrase_prog:
                phrase_progress_data = {
                    'currentPhraseIndex': phrase_prog.current_phrase_index,
                    'completedPhrases': phrase_prog.completed_phrases or [],
                    'totalPhrases': len(t.material_lines or []),
                    'isAllPhrasesCompleted': phrase_prog.is_all_phrases_completed,
                }

            payload.append({
                'id': str(t.id),
                'title': t.title,
                'description': t.description or "",
                'material': t.material_lines or [],
                'conversation': t.conversation_example or [],
                'phraseProgress': phrase_progress_data,
                'unlocked': t.sequence in unlocked_sequences,
                'completed': t.sequence in completed_sequences,
            })

        # Build user profile data
        user_profile_data = {
            'firstVisit': profile.first_visit,
            'lastVisitedTopicId': str(profile.last_visited_topic.id) if profile.last_visited_topic else None,
            'lastVisitedTopicTitle': profile.last_visited_topic.title if profile.last_visited_topic else "",
        }

        # Mark as not first visit after this request
        if profile.first_visit:
            profile.first_visit = False
            profile.save(update_fields=['first_visit'])

        response_data = {
            'topics': payload,
            'userProfile': user_profile_data
        }
        serializer = SpeakingTopicsResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Update last visited topic for welcome screen personalization"""
        topic_id = request.data.get('lastVisitedTopicId')
        if not topic_id:
            return Response({'detail': 'Missing lastVisitedTopicId'}, status=status.HTTP_400_BAD_REQUEST)

        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'first_visit': False}
        )
        profile.last_visited_topic = topic
        profile.save(update_fields=['last_visited_topic'])

        return Response({'success': True}, status=status.HTTP_200_OK)


class SubmitPhraseRecordingView(APIView):
    """Submit phrase recording for transcription and accuracy evaluation"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, topic_id):
        # Get topic and validate access
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)

        # Get required parameters
        phrase_index = request.data.get('phraseIndex')
        audio_file = request.data.get('audio')

        if phrase_index is None:
            return Response({'detail': 'Missing phraseIndex'}, status=status.HTTP_400_BAD_REQUEST)

        if not audio_file:
            return Response({'detail': 'Missing audio file'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            phrase_index = int(phrase_index)
        except (ValueError, TypeError):
            return Response({'detail': 'Invalid phraseIndex'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate phrase index
        material_lines = topic.material_lines or []
        if phrase_index < 0 or phrase_index >= len(material_lines):
            return Response({'detail': 'Invalid phraseIndex for this topic'}, status=status.HTTP_400_BAD_REQUEST)

        expected_phrase = material_lines[phrase_index]

        # Get or create phrase progress
        phrase_progress, _ = PhraseProgress.objects.get_or_create(
            user=request.user,
            topic=topic,
            defaults={'current_phrase_index': 0, 'completed_phrases': []}
        )

        # Transcribe audio with Whisper
        transcription = _transcribe_audio_with_whisper(audio_file)
        if not transcription:
            return Response({
                'success': False,
                'accuracy': 0.0,
                'transcription': '',
                'feedback': 'Could not process audio. Please try recording again.',
            }, status=status.HTTP_200_OK)

        # Calculate similarity
        accuracy = _calculate_similarity(expected_phrase, transcription)

        # Determine if passed (80% threshold)
        passed = accuracy >= 80.0
        next_phrase_index = None
        topic_completed = False
        xp_awarded = 0

        if passed:
            # Award XP
            xp_to_award = 50
            user_level, _ = UserLevel.objects.get_or_create(user=request.user)
            user_level.experience_points += xp_to_award
            user_level.total_points_earned += xp_to_award
            user_level.save()
            xp_awarded = xp_to_award

            # Mark phrase as completed and advance
            phrase_progress.mark_phrase_completed(phrase_index)
            next_phrase_index = phrase_progress.current_phrase_index

            # Check if all phrases completed
            if phrase_progress.is_all_phrases_completed:
                # Mark pronunciation mode complete and, for testing, auto-complete other modes
                topic_progress, _ = TopicProgress.objects.get_or_create(
                    user=request.user,
                    topic=topic
                )
                # Pronunciation mode done because all phrases are completed
                topic_progress.pronunciation_completed = True
                # TESTING TEMP: auto-mark remaining modes complete until those features are implemented
                topic_progress.fluency_completed = True
                topic_progress.vocabulary_completed = True
                topic_progress.listening_completed = True
                topic_progress.grammar_completed = True

                # Complete the topic only if all modes are completed
                if not topic_progress.completed and topic_progress.all_modes_completed:
                    topic_progress.completed = True
                    topic_progress.completed_at = timezone.now()
                topic_progress.save()
                topic_completed = topic_progress.completed

        # Get feedback from Gemini
        feedback = _get_gemini_feedback(expected_phrase, transcription, accuracy)

        # Persist user recording with audio and metadata
        recording_id = None
        audio_url = ''
        try:
            # Reset file pointer if needed before saving
            if hasattr(audio_file, 'seek'):
                try:
                    audio_file.seek(0)
                except Exception:
                    pass

            upr = UserPhraseRecording(
                user=request.user,
                topic=topic,
                phrase_index=phrase_index,
                transcription=transcription,
                accuracy=round(accuracy, 1),
                feedback=feedback,
            )
            # Save file to storage (uses upload_to path)
            try:
                filename = getattr(audio_file, 'name', 'recording.m4a')
                upr.audio_file.save(filename, audio_file, save=False)
            except Exception:
                # As a fallback, try reading content to a ContentFile
                try:
                    if hasattr(audio_file, 'seek'):
                        audio_file.seek(0)
                    content = audio_file.read()
                except Exception:
                    content = b''
                if content:
                    upr.audio_file.save('recording.m4a', ContentFile(content), save=False)
            upr.save()
            recording_id = str(upr.id)
            try:
                if upr.audio_file:
                    audio_url = request.build_absolute_uri(upr.audio_file.url)
            except Exception:
                audio_url = ''
        except Exception:
            # Do not fail the request if persistence fails; continue without recording info
            recording_id = None
            audio_url = ''

        # Build response
        result = {
            'success': passed,
            'accuracy': round(accuracy, 1),
            'transcription': transcription,
            'feedback': feedback,
            'nextPhraseIndex': next_phrase_index,
            'topicCompleted': topic_completed,
            'xpAwarded': xp_awarded,
            'recordingId': recording_id,
            'audioUrl': audio_url,
        }

        serializer = PhraseSubmissionResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompleteTopicView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        progress, created = TopicProgress.objects.get_or_create(user=request.user, topic=topic)
        # Mark all modes completed when manually completing a topic (keeps behavior consistent during testing)
        progress.pronunciation_completed = True
        progress.fluency_completed = True
        progress.vocabulary_completed = True
        progress.listening_completed = True
        progress.grammar_completed = True
        message = 'Topic marked as completed'
        if not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
        else:
            message = 'Topic already completed'
        progress.save()

        # Determine next topic to unlock
        next_topic = (
            Topic.objects.filter(is_active=True, sequence__gt=topic.sequence)
            .order_by('sequence')
            .first()
        )
        resp = {
            'success': True,
            'message': message,
            'completedTopicId': str(topic.id),
            'unlockedTopicId': str(next_topic.id) if next_topic else None,
        }
        serializer = CompleteTopicResponseSerializer(resp)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserPhraseRecordingsView(APIView):
    """List user's recordings for a topic, optionally filtered by phraseIndex"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        qs = UserPhraseRecording.objects.filter(user=request.user, topic=topic).order_by('-created_at')

        phrase_index = request.query_params.get('phraseIndex')
        if phrase_index is not None:
            try:
                idx = int(phrase_index)
                qs = qs.filter(phrase_index=idx)
            except (TypeError, ValueError):
                return Response({'detail': 'Invalid phraseIndex'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserPhraseRecordingSerializer(qs, many=True, context={'request': request})
        data = {'recordings': serializer.data}
        return Response(data, status=status.HTTP_200_OK)


class GenerateTTSView(APIView):
    """Generate TTS audio via Gemini and return a temporary WAV URL.

    Request JSON body:
      { "text": "Hello world", "voiceName": "Kore" }
    Response JSON body:
      { "audioUrl": "https://.../media/speaking_journey/tts/<id>.wav", "sampleRate": 24000, "voiceName": "Kore" }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text')
        voice_name = request.data.get('voiceName') or 'Kore'

        if not text or not isinstance(text, str) or not text.strip():
            return Response({'detail': 'Missing or invalid "text"'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Deterministic cache key and path
            sample_rate = 24000
            model_name = 'gemini-2.5-flash-preview-tts'
            text_norm = ' '.join(text.split())
            key_str = f"{model_name}|voice={voice_name}|rate={sample_rate}|text={text_norm}"
            cache_hash = hashlib.sha256(key_str.encode('utf-8')).hexdigest()
            relative_path = f"speaking_journey/tts/{cache_hash[:2]}/{cache_hash}.wav"

            # If file already exists, return it immediately (no external API call)
            if default_storage.exists(relative_path):
                try:
                    file_url = request.build_absolute_uri(default_storage.url(relative_path))
                except Exception:
                    base_url = request.build_absolute_uri(getattr(settings, 'MEDIA_URL', '/media/'))
                    file_url = base_url.rstrip('/') + '/' + relative_path.lstrip('/')
                return Response(
                    {
                        'audioUrl': file_url,
                        'sampleRate': sample_rate,
                        'voiceName': voice_name,
                        'cached': True,
                    },
                    status=status.HTTP_200_OK
                )

            api_key = (
                getattr(settings, 'GEMINI_API_KEY', '') or
                getattr(settings, 'GOOGLE_API_KEY', '') or
                os.environ.get('GEMINI_API_KEY', '') or
                os.environ.get('GOOGLE_API_KEY', '')
            )
            if not api_key:
                logger.error('Server misconfiguration: GEMINI_API_KEY/GOOGLE_API_KEY not set')
                return Response({'detail': 'Server misconfiguration: GEMINI_API_KEY/GOOGLE_API_KEY not set'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            url = (
                'https://generativelanguage.googleapis.com/v1beta/models/'
                'gemini-2.5-flash-preview-tts:generateContent'
            )

            payload = {
                'model': 'gemini-2.5-flash-preview-tts',
                'contents': [{
                    'parts': [{ 'text': text.strip() }]
                }],
                'generationConfig': {
                    'responseModalities': ['AUDIO'],
                    'speechConfig': {
                        'voiceConfig': {
                            'prebuiltVoiceConfig': { 'voiceName': voice_name }
                        }
                    }
                }
            }
            headers = {
                'x-goog-api-key': api_key,
                'Content-Type': 'application/json'
            }

            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            if resp.status_code != 200:
                detail = resp.text
                logger.error('Gemini TTS request failed', extra={'status_code': resp.status_code, 'body': detail[:1000]})
                return Response(
                    {'detail': 'Gemini TTS request failed', 'status': resp.status_code, 'body': detail[:800]},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            data = resp.json()
            try:
                b64 = (
                    data['candidates'][0]['content']['parts'][0]['inlineData']['data']
                )
            except Exception:
                return Response(
                    {'detail': 'Unexpected response format from Gemini', 'response': data},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            # Decode PCM (s16le, 24kHz, mono) to WAV
            pcm_bytes = base64.b64decode(b64)
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_bytes)
            wav_bytes = buf.getvalue()

            # Persist to media storage under deterministic cache path for HTTP streaming via GET
            saved_path = default_storage.save(relative_path, ContentFile(wav_bytes))
            try:
                file_url = request.build_absolute_uri(default_storage.url(saved_path))
            except Exception:
                # Fallback to constructing from MEDIA_URL
                base_url = request.build_absolute_uri(getattr(settings, 'MEDIA_URL', '/media/'))
                file_url = base_url.rstrip('/') + '/' + saved_path.lstrip('/')

            return Response(
                {
                    'audioUrl': file_url,
                    'sampleRate': sample_rate,
                    'voiceName': voice_name,
                    'cached': False,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception('TTS generation failed')
            return Response({'detail': 'TTS generation failed', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
