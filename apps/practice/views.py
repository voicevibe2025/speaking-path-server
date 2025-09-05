import random
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

        # Create submission; for now, we simulate immediate evaluation
        submission = PracticeSubmission.objects.create(
            user=request.user,
            prompt=prompt,
            audio_url=audio_url,
            status='EVALUATED',
            duration=30,
            score=round(random.uniform(60, 95), 1),
        )

        # Fake evaluation payload matching SpeakingEvaluation model
        evaluation_payload = {
            'sessionId': str(submission.id),
            'overallScore': submission.score or 75.0,
            'pronunciation': {'score': 80.0, 'level': 'GOOD', 'feedback': 'Clear pronunciation overall.'},
            'fluency': {'score': 78.0, 'level': 'GOOD', 'feedback': 'Smooth flow with minor pauses.'},
            'vocabulary': {'score': 74.0, 'level': 'GOOD', 'feedback': 'Good range; keep expanding.'},
            'grammar': {'score': 72.0, 'level': 'GOOD', 'feedback': 'Minor mistakes; mostly accurate.'},
            'coherence': {'score': 76.0, 'level': 'GOOD', 'feedback': 'Ideas are well organized.'},
            'culturalAppropriateness': None,
            'feedback': 'Great job! Focus on reducing filler words.',
            'suggestions': ['Practice linking words', 'Vary intonation'],
            'phoneticErrors': [
                {'word': 'comfortable', 'expected': 'kumf-tuh-buhl', 'actual': 'com-for-ta-ble', 'timestamp': 4.2}
            ],
            'pauses': [0.6, 1.4],
            'stutters': 0,
            'createdAt': timezone.now().isoformat(),
        }
        # For demo purposes, store a simulated transcript so the client UI can show it
        submission.transcription = "I am asking for directions to the museum. Could you tell me how to get there?"
        submission.evaluation = evaluation_payload
        submission.save(update_fields=['evaluation', 'transcription'])

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
