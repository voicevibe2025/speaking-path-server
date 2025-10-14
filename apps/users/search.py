"""
Unified search endpoint for VoiceVibe
Supports searching across Users, Groups, and Speaking Journey Topics
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from .models import UserProfile, Group
from .serializers import UserProfileSerializer, GroupSerializer
from apps.speaking_journey.models import Topic
from apps.speaking_journey.serializers import SpeakingTopicDtoSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_search(request):
    """
    Unified search across users, groups, and materials (speaking journey topics).
    
    Query params:
    - q or query: search term (required, min 2 chars)
    - type: optional filter - 'users', 'groups', 'materials', or 'all' (default: 'all')
    
    Returns:
    {
        "users": [...],
        "groups": [...],
        "materials": [...]
    }
    """
    try:
        # Get search query
        raw = (request.query_params.get('q') or request.query_params.get('query') or '').strip()
        if len(raw) < 2:
            return Response({
                'users': [],
                'groups': [],
                'materials': []
            }, status=status.HTTP_200_OK)
        
        # Get search type filter
        search_type = request.query_params.get('type', 'all').lower()
        
        result = {
            'users': [],
            'groups': [],
            'materials': []
        }
        
        # Search Users
        if search_type in ['all', 'users']:
            terms = [t for t in raw.split() if t]
            qs = UserProfile.objects.select_related('user')
            
            if terms:
                q = Q()
                for t in terms:
                    q |= Q(user__first_name__icontains=t)
                    q |= Q(user__last_name__icontains=t)
                    q |= Q(user__username__icontains=t)
                qs = qs.filter(q)
            else:
                qs = qs.filter(
                    Q(user__first_name__icontains=raw)
                    | Q(user__last_name__icontains=raw)
                    | Q(user__username__icontains=raw)
                )
            
            # Exclude blocked users
            qs = qs.exclude(user__blocked_by_relations__blocker=request.user) \
                   .exclude(user__blocking_relations__blocked_user=request.user)
            
            qs = qs.order_by('user__first_name', 'user__last_name')[:15]
            result['users'] = UserProfileSerializer(qs, many=True, context={'request': request}).data
        
        # Search Groups
        if search_type in ['all', 'groups']:
            groups_qs = Group.objects.filter(
                Q(display_name__icontains=raw)
                | Q(name__icontains=raw)
                | Q(description__icontains=raw)
            ).order_by('display_name')[:15]
            result['groups'] = GroupSerializer(groups_qs, many=True, context={'request': request}).data
        
        # Search Materials (Speaking Journey Topics)
        if search_type in ['all', 'materials']:
            topics_qs = Topic.objects.filter(
                Q(title__icontains=raw)
                | Q(description__icontains=raw),
                is_active=True
            ).order_by('sequence')[:15]
            
            # Build topic data similar to SpeakingTopicsView
            materials = []
            for topic in topics_qs:
                # Get user progress for this topic
                try:
                    from apps.speaking_journey.models import TopicProgress
                    progress = TopicProgress.objects.get(user=request.user, topic=topic)
                    unlocked = True
                    completed = progress.completed
                except TopicProgress.DoesNotExist:
                    # Check if should be unlocked
                    unlocked = _is_topic_unlocked(request.user, topic)
                    completed = False
                
                materials.append({
                    'id': str(topic.id),
                    'title': topic.title,
                    'description': topic.description,
                    'sequence': topic.sequence,
                    'unlocked': unlocked,
                    'completed': completed,
                    'type': 'material'
                })
            
            result['materials'] = materials
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _is_topic_unlocked(user, topic):
    """
    Check if a topic should be unlocked for the user.
    First topic is always unlocked, others require previous topic completion.
    """
    from apps.speaking_journey.models import Topic, TopicProgress
    
    # First topic is always unlocked
    first_topic = Topic.objects.filter(is_active=True).order_by('sequence').first()
    if first_topic and topic.id == first_topic.id:
        return True
    
    # Get previous topic by sequence
    previous_topic = Topic.objects.filter(
        sequence__lt=topic.sequence,
        is_active=True
    ).order_by('-sequence').first()
    
    if not previous_topic:
        return True
    
    # Check if previous topic is completed
    try:
        prev_progress = TopicProgress.objects.get(user=user, topic=previous_topic)
        return prev_progress.completed
    except TopicProgress.DoesNotExist:
        return False
