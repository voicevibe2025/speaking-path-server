from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Topic, TopicProgress, UserProfile
from .serializers import (
    SpeakingTopicsResponseSerializer,
    SpeakingTopicDtoSerializer,
    CompleteTopicResponseSerializer,
    UserProfileSerializer,
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

        # Get or create user profile for welcome screen personalization
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'first_visit': True}
        )

        payload = []
        for t in topics:
            payload.append({
                'id': str(t.id),
                'title': t.title,
                'description': t.description or "",
                'material': t.material_lines or [],
                'conversation': t.conversation_example or [],
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
