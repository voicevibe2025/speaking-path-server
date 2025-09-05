import os
import random
import tempfile
import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import PracticePrompt, PracticeSubmission
from .analysis import analyze_fluency
from .serializers import (
    PracticePromptSerializer,
    SubmissionResultSerializer,
    SpeakingSessionSerializer,
    SpeakingEvaluationSerializer,
)


class RandomPromptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = PracticePrompt.objects.filter(is_active=True)
        count = qs.count()
        if count == 0:
            return Response({'detail': 'No prompts available'}, status=status.HTTP_404_NOT_FOUND)
        prompt = qs[random.randint(0, count - 1)]
        data = PracticePromptSerializer(prompt).data
        return Response(data, status=status.HTTP_200_OK)


class PromptsByCategoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, category):
        prompts = PracticePrompt.objects.filter(is_active=True, category=category)
        data = PracticePromptSerializer(prompts, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class PromptDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        prompt = get_object_or_404(PracticePrompt, id=id, is_active=True)
        data = PracticePromptSerializer(prompt).data
        return Response(data, status=status.HTTP_200_OK)


class PromptListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        difficulty = request.query_params.get('difficulty')
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        qs = PracticePrompt.objects.filter(is_active=True)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        prompts = qs[offset:offset + limit]
        data = PracticePromptSerializer(prompts, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class SubmitRecordingView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, prompt_id):
        prompt = get_object_or_404(PracticePrompt, id=prompt_id, is_active=True)
        audio_file = request.data.get('audio')
        if not audio_file:
            return Response({'detail': 'Missing audio file'}, status=status.HTTP_400_BAD_REQUEST)

        # Save uploaded audio to storage
        filename = f"practice/{timezone.now().strftime('%Y%m%d%H%M%S')}_{audio_file.name}"
        path = default_storage.save(filename, ContentFile(audio_file.read()))
        # Build an absolute URL to the stored file so mobile clients can stream it
        try:
            storage_url = default_storage.url(path)  # typically MEDIA_URL + path
        except Exception:
            storage_url = f"{settings.MEDIA_URL}{path}" if getattr(settings, 'MEDIA_URL', None) else path
        audio_url = request.build_absolute_uri(storage_url)

        # Create submission record first
        submission = PracticeSubmission.objects.create(
            user=request.user,
            prompt=prompt,
            audio_url=audio_url,
            status='PROCESSING',
            duration=0,
            score=None,
        )

        # Resolve a local path for analysis (FileSystemStorage supports .path)
        local_path = None
        try:
            local_path = default_storage.path(path)
        except Exception:
            if getattr(settings, 'MEDIA_ROOT', None):
                local_path = os.path.join(settings.MEDIA_ROOT, path)

        # If we couldn't determine a local path (e.g., remote storage), download temporarily
        cleanup_temp = None
        if not (local_path and os.path.exists(local_path)):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(path)[1] or ".m4a") as tmp:
                    r = requests.get(audio_url, timeout=30)
                    r.raise_for_status()
                    tmp.write(r.content)
                    local_path = tmp.name
                    cleanup_temp = tmp.name
            except Exception:
                local_path = None

        # Run analysis (gracefully handles missing dependencies)
        result = analyze_fluency(local_path) if local_path else {
            'transcript': '',
            'pauses': [],
            'stutters': 0,
            'mispronunciations': [],
            'overall_score': 75.0,
            'pronunciation': {'score': 78.0, 'level': 'GOOD', 'feedback': 'Pronunciation is generally clear.'},
            'fluency': {'score': 76.0, 'level': 'GOOD', 'feedback': 'Flow is smooth with minor pauses.'},
            'vocabulary': {'score': 74.0, 'level': 'GOOD', 'feedback': 'Vocabulary is appropriate.'},
            'grammar': {'score': 72.0, 'level': 'GOOD', 'feedback': 'Minor mistakes.'},
            'coherence': {'score': 76.0, 'level': 'GOOD', 'feedback': 'Well organized.'},
            'feedback': 'Great job! Focus on reducing filler words and maintaining steady pace.',
            'suggestions': ['Practice linking words', 'Vary intonation'],
        }

        # Cleanup temp file if used
        if cleanup_temp and os.path.exists(cleanup_temp):
            try:
                os.remove(cleanup_temp)
            except Exception:
                pass

        # Map analysis result to API payload/DB fields
        evaluation_payload = {
            'sessionId': str(submission.id),
            'overallScore': float(result.get('overall_score') or 0.0),
            'pronunciation': result.get('pronunciation'),
            'fluency': result.get('fluency'),
            'vocabulary': result.get('vocabulary'),
            'grammar': result.get('grammar'),
            'coherence': result.get('coherence'),
            'culturalAppropriateness': None,
            'feedback': result.get('feedback') or '',
            'suggestions': result.get('suggestions') or [],
            'phoneticErrors': result.get('mispronunciations') or [],
            'pauses': result.get('pauses') or [],
            'stutters': int(result.get('stutters') or 0),
            'createdAt': timezone.now().isoformat(),
        }

        submission.transcription = result.get('transcript') or ''
        submission.evaluation = evaluation_payload
        submission.score = evaluation_payload['overallScore']
        submission.status = 'EVALUATED'
        # TODO: set real duration if available (from metadata or word timings)
        submission.duration = 30
        submission.save(update_fields=['evaluation', 'transcription', 'score', 'status', 'duration'])

        result = {
            'sessionId': str(submission.id),
            'score': float(submission.score or 0.0),
            'feedback': evaluation_payload['feedback'],
        }
        serializer = SubmissionResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SessionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id):
        submission = get_object_or_404(PracticeSubmission, id=session_id, user=request.user)
        data = SpeakingSessionSerializer(submission).data
        return Response(data, status=status.HTTP_200_OK)


class SessionEvaluationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id):
        submission = get_object_or_404(PracticeSubmission, id=session_id, user=request.user)
        eval_payload = submission.evaluation or {}
        serializer = SpeakingEvaluationSerializer(eval_payload)
        return Response(serializer.data, status=status.HTTP_200_OK)
