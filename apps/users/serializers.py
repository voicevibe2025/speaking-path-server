"""
User profile serializers for VoiceVibe
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.authentication.models import User
from .models import UserProfile, LearningPreference, UserAchievement
from apps.gamification.serializers import UserBadgeSerializer

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

    def get_total_practice_hours(self, obj):
        """Convert practice time from minutes to hours"""
        if hasattr(obj.user, 'analytics') and obj.user.analytics.total_practice_time_minutes:
            return round(obj.user.analytics.total_practice_time_minutes / 60, 1)
        return 0

    def get_recent_achievements(self, obj):
        """Get the 3 most recent achievements earned by the user"""
        recent_badges = obj.user.earned_badges.select_related('badge').order_by('-earned_at')[:3]
        return UserBadgeSerializer(recent_badges, many=True).data

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
            'last_practice_date',
            'created_at', 'updated_at', 'recent_achievements'
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
