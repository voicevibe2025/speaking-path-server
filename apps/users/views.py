"""
User profile views for VoiceVibe
"""
from datetime import date, timedelta
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from apps.speaking_journey.models import TopicProgress

from apps.authentication.models import User
from .models import UserProfile, LearningPreference, UserAchievement, UserFollow, UserBlock, Report, PrivacySettings
from .serializers import (
    UserProfileSerializer,
    LearningPreferenceSerializer,
    UserAchievementSerializer,
    UserStatsSerializer,
    PrivacySettingsSerializer,
    ReportSerializer,
    BlockedUserSerializer
)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class UserProfileDetailView(generics.RetrieveAPIView):
    """
    Retrieve any user profile by user ID
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'user__id'
    lookup_url_kwarg = 'user_id'

    def get_queryset(self):
        return UserProfile.objects.select_related('user')

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            profile, created = UserProfile.objects.get_or_create(user=user)
            return profile
        except User.DoesNotExist:
            from django.http import Http404
            raise Http404("User not found")


class LearningPreferenceView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update learning preferences
    """
    serializer_class = LearningPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        preference, created = LearningPreference.objects.get_or_create(user=self.request.user)
        return preference


class UserAchievementListView(generics.ListAPIView):
    """
    List all user achievements
    """
    serializer_class = UserAchievementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAchievement.objects.filter(user=self.request.user).order_by('-created_at')


class UserAchievementDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific user achievement
    """
    serializer_class = UserAchievementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAchievement.objects.filter(user=self.request.user)


class UserStatsView(generics.RetrieveAPIView):
    """
    Retrieve user statistics summary
    """
    serializer_class = UserStatsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        profile = get_object_or_404(UserProfile, user=user)

        # Calculate total points from achievements
        total_points = UserAchievement.objects.filter(
            user=user,
            is_completed=True
        ).aggregate(total=Sum('points_earned'))['total'] or 0

        # Count completed achievements
        completed_achievements = UserAchievement.objects.filter(
            user=user,
            is_completed=True
        ).count()

        # Compute proficiency from Speaking Journey topics mastered
        try:
            topics_mastered = TopicProgress.objects.filter(user=user, completed=True).count()
        except Exception:
            topics_mastered = 0
        if topics_mastered <= 10:
            proficiency = "Chaucerite 🌱"
        elif topics_mastered <= 20:
            proficiency = "Shakespire 🎭"
        elif topics_mastered <= 30:
            proficiency = "Miltonarch 🔥"
        elif topics_mastered <= 40:
            proficiency = "Austennova 💫"
        elif topics_mastered <= 50:
            proficiency = "Dickenlord 📚"
        elif topics_mastered <= 60:
            proficiency = "Joycemancer 🌀"
        else:
            proficiency = "The Bard Eternal 👑"

        return {
            'total_practice_time': profile.total_practice_time,
            'streak_days': profile.streak_days,
            'current_proficiency': proficiency,
            'completed_achievements': completed_achievements,
            'total_points': total_points,
            'last_practice_date': profile.last_practice_date,
        }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_streak(request):
    """
    Update user's streak count
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        today = date.today()

        # If last practice was yesterday, increment streak
        if profile.last_practice_date == today - timedelta(days=1):
            profile.streak_days += 1
        # If last practice was today, keep streak the same
        elif profile.last_practice_date == today:
            pass  # No change needed
        # If last practice was more than yesterday, reset streak
        else:
            profile.streak_days = 1

        profile.last_practice_date = today
        profile.save()

        return Response({
            'success': True,
            'streak_days': profile.streak_days,
            'last_practice_date': profile.last_practice_date
        })

    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    """
    Search users by first name, last name, or username.
    Accepts 'q' or 'query' query params. Returns up to 25 matches.
    """
    try:
        raw = (request.query_params.get('q') or request.query_params.get('query') or '').strip()
        if not raw:
            return Response([], status=status.HTTP_200_OK)

        terms = [t for t in raw.split() if t]
        qs = UserProfile.objects.select_related('user')
        if terms:
            # Match any term across first_name, last_name, username
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

        qs = qs.order_by('user__first_name', 'user__last_name')[:25]
        serializer = UserProfileSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def follow_toggle(request, user_id):
    """
    POST -> Follow the user with id=user_id
    DELETE -> Unfollow the user with id=user_id
    Returns JSON with success flag, isFollowing state, and follower/following counts for the target user.
    """
    if request.user.id == int(user_id):
        return Response({'error': "You can't follow yourself"}, status=status.HTTP_400_BAD_REQUEST)

    target_user = get_object_or_404(User, id=user_id)

    try:
        if request.method == 'POST':
            follow, created = UserFollow.objects.get_or_create(follower=request.user, following=target_user)
            is_following = True
            # Emit notification when a new follow is created
            if created:
                from apps.social.models import Notification
                Notification.objects.create(
                    recipient=target_user,
                    actor=request.user,
                    type='user_follow',
                    post=None,
                    comment=None,
                )
        else:  # DELETE
            UserFollow.objects.filter(follower=request.user, following=target_user).delete()
            is_following = False

        followers_count = UserFollow.objects.filter(following=target_user).count()
        following_count = UserFollow.objects.filter(follower=target_user).count()

        return Response({
            'success': True,
            'isFollowing': is_following,
            'followersCount': followers_count,
            'followingCount': following_count,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_followers(request, user_id=None):
    """
    List followers for a given user_id, or current user if user_id is None.
    """
    target_user = request.user if user_id is None else get_object_or_404(User, id=user_id)
    follower_ids = UserFollow.objects.filter(following=target_user).values_list('follower_id', flat=True)
    profiles = UserProfile.objects.filter(user_id__in=follower_ids).select_related('user')
    serializer = UserProfileSerializer(profiles, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_following(request, user_id=None):
    """
    List accounts the given user_id is following, or current user if user_id is None.
    """
    target_user = request.user if user_id is None else get_object_or_404(User, id=user_id)
    following_ids = UserFollow.objects.filter(follower=target_user).values_list('following_id', flat=True)
    profiles = UserProfile.objects.filter(user_id__in=following_ids).select_related('user')
    serializer = UserProfileSerializer(profiles, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_practice_time(request):
    """
    Add practice time to user's total
    """
    try:
        minutes = request.data.get('minutes', 0)

        if not isinstance(minutes, (int, float)) or minutes <= 0:
            return Response(
                {'error': 'Invalid minutes value'},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile = UserProfile.objects.get(user=request.user)
        profile.total_practice_time += int(minutes)
        profile.save()

        return Response({
            'success': True,
            'total_practice_time': profile.total_practice_time,
            'added_minutes': int(minutes)
        })

    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password endpoint
    Expects: old_password, new_password
    """
    try:
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'error': 'Both old_password and new_password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if old password is correct
        if not request.user.check_password(old_password):
            return Response(
                {'error': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate new password length
        if len(new_password) < 6:
            return Response(
                {'error': 'New password must be at least 6 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        request.user.set_password(new_password)
        request.user.save()

        return Response({
            'success': True,
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """
    Delete the current user's account and all associated data.
    This is a permanent action that cannot be undone.
    """
    try:
        user = request.user
        
        # Log the deletion for audit purposes
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'User {user.id} ({user.email}) requested account deletion')
        
        # Delete user account (cascade will handle related data)
        user_email = user.email
        user.delete()
        
        logger.info(f'Account deleted successfully for {user_email}')
        
        return Response({
            'success': True,
            'message': 'Account deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error deleting account: {str(e)}')
        return Response(
            {'error': 'Failed to delete account'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Privacy Settings Views
class PrivacySettingsView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update user privacy settings
    """
    serializer_class = PrivacySettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        settings, created = PrivacySettings.objects.get_or_create(user=self.request.user)
        return settings


# Blocking Views
@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def block_user(request, user_id):
    """
    POST -> Block a user
    DELETE -> Unblock a user
    """
    if request.user.id == int(user_id):
        return Response({'error': "You can't block yourself"}, status=status.HTTP_400_BAD_REQUEST)

    target_user = get_object_or_404(User, id=user_id)

    try:
        if request.method == 'POST':
            reason = request.data.get('reason', '')
            block, created = UserBlock.objects.get_or_create(
                blocker=request.user,
                blocked_user=target_user,
                defaults={'reason': reason}
            )
            # Also unfollow if following
            UserFollow.objects.filter(follower=request.user, following=target_user).delete()
            UserFollow.objects.filter(follower=target_user, following=request.user).delete()
            
            return Response({
                'success': True,
                'message': 'User blocked successfully',
                'isBlocked': True
            })
        else:  # DELETE
            UserBlock.objects.filter(blocker=request.user, blocked_user=target_user).delete()
            return Response({
                'success': True,
                'message': 'User unblocked successfully',
                'isBlocked': False
            })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_blocked_users(request):
    """
    List all users blocked by the current user
    """
    try:
        blocks = UserBlock.objects.filter(blocker=request.user).select_related('blocked_user').order_by('-created_at')
        serializer = BlockedUserSerializer(blocks, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Reporting Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_report(request):
    """
    Create a new report for a user, post, or comment
    """
    try:
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            # Prevent self-reporting for user reports
            if serializer.validated_data.get('report_type') == 'user':
                reported_user = serializer.validated_data.get('reported_user')
                if reported_user == request.user:
                    return Response(
                        {'error': "You can't report yourself"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            serializer.save(reporter=request.user)
            return Response({
                'success': True,
                'message': 'Report submitted successfully. Our moderation team will review it.',
                'report': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_reports(request):
    """
    List all reports created by the current user
    """
    try:
        reports = Report.objects.filter(reporter=request.user).order_by('-created_at')
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
