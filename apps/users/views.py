"""
User profile views for VoiceVibe
"""
from datetime import date, timedelta
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.models import User
from .models import UserProfile, LearningPreference, UserAchievement
from .serializers import (
    UserProfileSerializer,
    LearningPreferenceSerializer,
    UserAchievementSerializer,
    UserStatsSerializer
)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


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

        return {
            'total_practice_time': profile.total_practice_time,
            'streak_days': profile.streak_days,
            'current_proficiency': profile.current_proficiency,
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
