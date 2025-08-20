"""
Views for speaking practice sessions
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import PracticeSession, AudioRecording, SessionFeedback
from .serializers import (
    PracticeSessionSerializer,
    PracticeSessionCreateSerializer,
    PracticeSessionUpdateSerializer,
    SessionSummarySerializer,
    SessionStatisticsSerializer,
    AudioRecordingSerializer,
    SessionFeedbackSerializer
)


class PracticeSessionListCreateView(generics.ListCreateAPIView):
    """
    List all practice sessions or create a new one
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter sessions by authenticated user"""
        return PracticeSession.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PracticeSessionCreateSerializer
        return SessionSummarySerializer


class PracticeSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a practice session
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PracticeSession.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PracticeSessionUpdateSerializer
        return PracticeSessionSerializer

    def get_object(self):
        """Get session by session_id instead of pk"""
        session_id = self.kwargs.get('session_id')
        return get_object_or_404(
            PracticeSession,
            session_id=session_id,
            user=self.request.user
        )


class SessionStatisticsView(APIView):
    """
    Get practice session statistics for the authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get comprehensive statistics
        """
        user = request.user

        # Date range filtering
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        # Get sessions in date range
        sessions = PracticeSession.objects.filter(
            user=user,
            started_at__gte=start_date
        )

        # Calculate statistics
        stats = sessions.aggregate(
            total_sessions=Count('id'),
            completed_sessions=Count('id', filter=Q(session_status='completed')),
            total_practice_time=Sum('duration_seconds'),
            average_session_duration=Avg('duration_seconds'),
            average_overall_score=Avg('overall_score'),
            average_pronunciation_score=Avg('pronunciation_score'),
            average_fluency_score=Avg('fluency_score'),
            average_grammar_score=Avg('grammar_score'),
            average_vocabulary_score=Avg('vocabulary_score')
        )

        # Sessions by type
        sessions_by_type = {}
        for session_type, _ in PracticeSession.SESSION_TYPES:
            count = sessions.filter(session_type=session_type).count()
            if count > 0:
                sessions_by_type[session_type] = count

        # Recent sessions
        recent_sessions = sessions.order_by('-started_at')[:5]

        # Calculate improvement trend (compare first half vs second half)
        mid_point = sessions.count() // 2
        if mid_point > 0:
            first_half = sessions.order_by('started_at')[:mid_point]
            second_half = sessions.order_by('started_at')[mid_point:]

            first_avg = first_half.aggregate(
                avg_score=Avg('overall_score')
            )['avg_score'] or 0

            second_avg = second_half.aggregate(
                avg_score=Avg('overall_score')
            )['avg_score'] or 0

            improvement = ((second_avg - first_avg) / max(first_avg, 1)) * 100 if first_avg > 0 else 0
        else:
            improvement = 0

        # Prepare response data
        data = {
            **stats,
            'sessions_by_type': sessions_by_type,
            'recent_sessions': SessionSummarySerializer(recent_sessions, many=True).data,
            'improvement_trend': {
                'percentage': round(improvement, 2),
                'direction': 'up' if improvement > 0 else 'down' if improvement < 0 else 'stable'
            }
        }

        # Handle None values
        for key, value in data.items():
            if value is None and key not in ['sessions_by_type', 'recent_sessions', 'improvement_trend']:
                data[key] = 0

        serializer = SessionStatisticsSerializer(data)
        return Response(serializer.data)


class AudioRecordingListView(generics.ListAPIView):
    """
    List audio recordings for a session
    """
    serializer_class = AudioRecordingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        session_id = self.kwargs.get('session_id')
        return AudioRecording.objects.filter(
            session__session_id=session_id,
            session__user=self.request.user
        ).order_by('sequence_number')


class SessionFeedbackListView(generics.ListAPIView):
    """
    List feedback items for a session
    """
    serializer_class = SessionFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        session_id = self.kwargs.get('session_id')
        return SessionFeedback.objects.filter(
            session__session_id=session_id,
            session__user=self.request.user
        ).order_by('feedback_type', '-severity')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_session(request):
    """
    Start a new practice session
    """
    serializer = PracticeSessionCreateSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        session = serializer.save()
        return Response(
            PracticeSessionSerializer(session).data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def end_session(request, session_id):
    """
    End a practice session and calculate final scores
    """
    try:
        session = PracticeSession.objects.get(
            session_id=session_id,
            user=request.user
        )
    except PracticeSession.DoesNotExist:
        return Response(
            {'error': 'Session not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if session.session_status == 'completed':
        return Response(
            {'error': 'Session already completed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update session status
    session.session_status = 'completed'
    session.completed_at = timezone.now()

    # Calculate duration
    if session.started_at:
        duration = (session.completed_at - session.started_at).total_seconds()
        session.duration_seconds = int(duration)

    # Calculate scores (placeholder - would use AI evaluation service)
    if not session.overall_score:
        # Average of individual scores if they exist
        scores = [
            session.pronunciation_score or 0,
            session.fluency_score or 0,
            session.grammar_score or 0,
            session.vocabulary_score or 0
        ]
        valid_scores = [s for s in scores if s > 0]
        if valid_scores:
            session.overall_score = sum(valid_scores) / len(valid_scores)

    session.save()

    return Response(
        PracticeSessionSerializer(session).data,
        status=status.HTTP_200_OK
    )
