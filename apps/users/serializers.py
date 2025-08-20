"""
User profile serializers for VoiceVibe
"""
from rest_framework import serializers
from apps.authentication.models import User
from .models import UserProfile, LearningPreference, UserAchievement


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'date_of_birth', 'phone_number', 'avatar_url', 'bio',
            'native_language', 'target_language', 'current_proficiency',
            'learning_goal', 'daily_practice_goal', 'preferred_session_duration',
            'power_distance_preference', 'individualism_preference',
            'masculinity_preference', 'uncertainty_avoidance_preference',
            'long_term_orientation_preference',
            'preferred_reward_type', 'enable_notifications', 'enable_reminders',
            'total_practice_time', 'streak_days', 'last_practice_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'total_practice_time', 'streak_days', 'created_at', 'updated_at']


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
