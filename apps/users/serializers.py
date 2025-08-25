"""
User profile serializers for VoiceVibe
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange

from apps.authentication.models import User
from .models import UserProfile, LearningPreference, UserAchievement
from apps.gamification.serializers import UserBadgeSerializer
from apps.speaking_sessions.models import PracticeSession
from apps.learning_paths.models import UserProgress

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_name = serializers.CharField(source='user.username', allow_blank=True, required=False)
    user_email = serializers.EmailField(source='user.email', allow_blank=True, required=False)

    # Gamification fields from UserLevel model
    current_level = serializers.IntegerField(source='user.level_profile.current_level', read_only=True)
    experience_points = serializers.IntegerField(source='user.level_profile.experience_points', read_only=True)
    streak_days = serializers.IntegerField(source='user.level_profile.streak_days', read_only=True)

    # Quick Stats from UserAnalytics model
    total_practice_hours = serializers.SerializerMethodField()
    lessons_completed = serializers.IntegerField(source='user.analytics.scenarios_completed', read_only=True)
    recordings_count = serializers.IntegerField(source='user.analytics.total_sessions_completed', read_only=True)
    avg_score = serializers.FloatField(source='user.analytics.overall_proficiency_score', read_only=True)

    # Recent Achievements from UserBadge model
    recent_achievements = serializers.SerializerMethodField()

    # Learning Preferences from UserProfile model
    daily_practice_goal = serializers.IntegerField(read_only=True)
    learning_goal = serializers.CharField(read_only=True)
    target_language = serializers.CharField(read_only=True)

    # Skill Progress from UserAnalytics model
    speaking_score = serializers.FloatField(source='user.analytics.fluency_score', read_only=True)
    listening_score = serializers.FloatField(source='user.analytics.coherence_score', read_only=True)
    grammar_score = serializers.FloatField(source='user.analytics.grammar_score', read_only=True)
    vocabulary_score = serializers.FloatField(source='user.analytics.vocabulary_score', read_only=True)
    pronunciation_score = serializers.FloatField(source='user.analytics.pronunciation_score', read_only=True)

    # Monthly Progress
    monthly_days_active = serializers.SerializerMethodField()
    monthly_xp_earned = serializers.SerializerMethodField()
    monthly_lessons_completed = serializers.SerializerMethodField()

    def get_total_practice_hours(self, obj):
        """Convert practice time from minutes to hours"""
        if hasattr(obj.user, 'analytics') and obj.user.analytics.total_practice_time_minutes:
            return round(obj.user.analytics.total_practice_time_minutes / 60, 1)
        return 0

    def get_recent_achievements(self, obj):
        """Get the 3 most recent achievements earned by the user"""
        recent_badges = obj.user.earned_badges.select_related('badge').order_by('-earned_at')[:3]
        return UserBadgeSerializer(recent_badges, many=True).data

    def get_monthly_days_active(self, obj):
        """Get the number of days the user was active in the current month"""
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        _, last_day = monthrange(today.year, today.month)
        end_of_month = today.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

        # Count distinct dates with practice sessions
        return PracticeSession.objects.filter(
            user=obj.user,
            started_at__gte=start_of_month,
            started_at__lte=end_of_month,
            session_status='completed'
        ).dates('started_at', 'day').count()

    def get_monthly_xp_earned(self, obj):
        """Get the total XP earned by the user in the current month"""
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        _, last_day = monthrange(today.year, today.month)
        end_of_month = today.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

        # Calculate XP from completed practice sessions (assume 10-50 XP per session based on score)
        monthly_sessions = PracticeSession.objects.filter(
            user=obj.user,
            started_at__gte=start_of_month,
            started_at__lte=end_of_month,
            session_status='completed'
        )

        total_xp = 0
        for session in monthly_sessions:
            # Base XP calculation: 10 XP + bonus based on overall_score
            base_xp = 10
            if session.overall_score:
                bonus_xp = int(session.overall_score * 0.4)  # Up to 40 XP bonus for perfect score
                total_xp += base_xp + bonus_xp
            else:
                total_xp += base_xp

        return total_xp

    def get_monthly_lessons_completed(self, obj):
        """Get the number of lessons completed by the user in the current month"""
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        _, last_day = monthrange(today.year, today.month)
        end_of_month = today.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

        # Count completed learning activities
        return UserProgress.objects.filter(
            user=obj.user,
            status='completed',
            completed_at__gte=start_of_month,
            completed_at__lte=end_of_month
        ).count()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_email', 'user_name', 'first_name', 'last_name',
            'date_of_birth', 'phone_number', 'avatar_url', 'bio',
            'native_language', 'target_language', 'current_proficiency',
            'learning_goal', 'daily_practice_goal', 'preferred_session_duration',
            'power_distance_preference', 'individualism_preference',
            'masculinity_preference', 'uncertainty_avoidance_preference',
            'long_term_orientation_preference',
            'preferred_reward_type', 'enable_notifications', 'enable_reminders',
            'total_practice_time', 'current_level', 'experience_points', 'streak_days',
            'total_practice_hours', 'lessons_completed', 'recordings_count', 'avg_score',
            'daily_practice_goal', 'learning_goal', 'target_language',
            'speaking_score', 'listening_score', 'grammar_score', 'vocabulary_score', 'pronunciation_score',
            'last_practice_date',
            'created_at', 'updated_at', 'recent_achievements',
            'monthly_days_active', 'monthly_xp_earned', 'monthly_lessons_completed'
        ]
        read_only_fields = ['id', 'user', 'total_practice_time', 'created_at', 'updated_at']


class LearningPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for learning preferences
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = LearningPreference
        fields = [
            'id', 'user', 'user_email',
            'preferred_scenarios', 'avoided_topics',
            'visual_learning', 'auditory_learning', 'kinesthetic_learning',
            'immediate_correction', 'detailed_feedback', 'cultural_context',
            'ai_personality', 'difficulty_adaptation_speed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UserAchievementSerializer(serializers.ModelSerializer):
    """
    Serializer for user achievements
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserAchievement
        fields = [
            'id', 'user', 'user_email',
            'achievement_type', 'achievement_name', 'achievement_description',
            'category', 'points_earned', 'badge_image_url',
            'progress_current', 'progress_target', 'is_completed',
            'completion_percentage',
            'earned_at', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

    def get_completion_percentage(self, obj):
        """Calculate completion percentage"""
        if obj.progress_target == 0:
            return 0
        return min(100, int((obj.progress_current / obj.progress_target) * 100))


class UserStatsSerializer(serializers.Serializer):
    """
    Serializer for user statistics summary
    """
    total_practice_time = serializers.IntegerField()
    streak_days = serializers.IntegerField()
    current_proficiency = serializers.CharField()
    completed_achievements = serializers.IntegerField()
    total_points = serializers.IntegerField()
    last_practice_date = serializers.DateField(allow_null=True)

    class Meta:
        fields = '__all__'
