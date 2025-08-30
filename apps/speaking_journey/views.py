from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Topic, TopicProgress
from .serializers import (
    SpeakingTopicsResponseSerializer,
    SpeakingTopicDtoSerializer,
    CompleteTopicResponseSerializer,
)


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


class SpeakingTopicsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        topics, completed_sequences, unlocked_sequences = _compute_unlocks(request.user)
        payload = []
        for t in topics:
            payload.append({
                'id': str(t.id),
                'title': t.title,
                'material': t.material_lines or [],
                'unlocked': t.sequence in unlocked_sequences,
                'completed': t.sequence in completed_sequences,
            })
        serializer = SpeakingTopicsResponseSerializer({'topics': payload})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompleteTopicView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        progress, created = TopicProgress.objects.get_or_create(user=request.user, topic=topic)
        message = 'Topic marked as completed'
        if not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
            progress.save()
        else:
            message = 'Topic already completed'

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
