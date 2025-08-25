"""
User profile serializers for VoiceVibe
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum
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

    # Quick Stats calculated from existing models
    total_practice_hours = serializers.SerializerMethodField()
    lessons_completed = serializers.SerializerMethodField()
    recordings_count = serializers.SerializerMethodField()
    avg_score = serializers.SerializerMethodField()

    # Recent Achievements from UserBadge model
    recent_achievements = serializers.SerializerMethodField()

    # Learning Preferences from UserProfile model
    daily_practice_goal = serializers.IntegerField(read_only=True)
    learning_goal = serializers.CharField(read_only=True)
    target_language = serializers.CharField(read_only=True)

    def get_total_practice_hours(self, obj):
        """Calculate total practice hours from PracticeSession durations"""
        if hasattr(obj, 'user') and obj.user:
            # Sum duration from completed practice sessions
            from apps.speaking_sessions.models import PracticeSession
            total_seconds = PracticeSession.objects.filter(
                user=obj.user,
                session_status='completed'
            ).aggregate(
                total=Sum('duration_seconds')
            )['total'] or 0

            # Convert seconds to hours, rounded to 1 decimal place
            return round(total_seconds / 3600, 1)
        return 0.0

    def get_lessons_completed(self, obj):
        """Calculate completed lessons from UserProgress"""
        if hasattr(obj, 'user') and obj.user:
            from apps.learning_paths.models import UserProgress
            return UserProgress.objects.filter(
                user=obj.user,
                status='completed'
            ).count()
        return 0

    def get_recordings_count(self, obj):
        """Calculate total recordings from PracticeSession count"""
        if hasattr(obj, 'user') and obj.user:
            from apps.speaking_sessions.models import PracticeSession
            return PracticeSession.objects.filter(
                user=obj.user,
                session_status='completed'
            ).count()
        return 0

    def get_avg_score(self, obj):
        """Calculate average score from completed PracticeSession overall scores"""
        if hasattr(obj, 'user') and obj.user:
            from apps.speaking_sessions.models import PracticeSession
            avg_data = PracticeSession.objects.filter(
                user=obj.user,
                session_status='completed',
                overall_score__isnull=False
            ).aggregate(
                avg_score=Avg('overall_score')
            )

            avg_score = avg_data.get('avg_score')
            return round(avg_score, 1) if avg_score else 0.0
        return 0.0

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
