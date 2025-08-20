"""
Serializers for Learning Paths
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    LearningPath,
    LearningModule,
    ModuleActivity,
    UserProgress,
    Milestone,
    UserMilestone
)

User = get_user_model()


class ModuleActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for module activities
    """
    class Meta:
        model = ModuleActivity
        fields = [
            'activity_id', 'name', 'description', 'activity_type',
            'order_index', 'instructions', 'content', 'resources',
            'estimated_duration_minutes', 'points', 'passing_score',
            'requires_ai_evaluation', 'ai_evaluation_criteria',
            'cultural_notes', 'indonesian_context',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['activity_id', 'created_at', 'updated_at']


class LearningModuleSerializer(serializers.ModelSerializer):
    """
    Serializer for learning modules
    """
    activities = ModuleActivitySerializer(many=True, read_only=True)
    activities_count = serializers.IntegerField(source='activities.count', read_only=True)

    class Meta:
        model = LearningModule
        fields = [
            'module_id', 'learning_path', 'name', 'description',
            'module_type', 'order_index', 'learning_objectives',
            'prerequisites', 'content', 'estimated_duration_minutes',
            'minimum_score', 'max_attempts', 'is_locked', 'is_completed',
            'completion_percentage', 'activities', 'activities_count',
            'created_at', 'unlocked_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'module_id', 'created_at', 'activities', 'activities_count'
        ]


class LearningPathSerializer(serializers.ModelSerializer):
    """
    Serializer for learning paths
    """
    modules = LearningModuleSerializer(many=True, read_only=True)
    modules_count = serializers.IntegerField(source='modules.count', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = LearningPath
        fields = [
            'path_id', 'user', 'user_email', 'name', 'description',
            'path_type', 'difficulty_level', 'learning_goal',
            'estimated_duration_weeks', 'target_proficiency',
            'is_active', 'progress_percentage', 'current_module_index',
            'focus_areas', 'cultural_context', 'modules', 'modules_count',
            'created_at', 'started_at', 'completed_at', 'last_accessed'
        ]
        read_only_fields = [
            'path_id', 'user', 'user_email', 'modules',
            'modules_count', 'created_at'
        ]

    def create(self, validated_data):
        """
        Create learning path with user from request context
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for user progress
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    path_name = serializers.CharField(source='learning_path.name', read_only=True)
    module_name = serializers.CharField(source='module.name', read_only=True, allow_null=True)
    activity_name = serializers.CharField(source='activity.name', read_only=True, allow_null=True)

    class Meta:
        model = UserProgress
        fields = [
            'id', 'user', 'user_email', 'learning_path', 'path_name',
            'module', 'module_name', 'activity', 'activity_name',
            'status', 'score', 'attempts', 'time_spent_minutes',
            'results', 'ai_feedback', 'started_at', 'completed_at',
            'last_attempt_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'path_name',
            'module_name', 'activity_name'
        ]


class MilestoneSerializer(serializers.ModelSerializer):
    """
    Serializer for milestones
    """
    path_name = serializers.CharField(source='learning_path.name', read_only=True, allow_null=True)

    class Meta:
        model = Milestone
        fields = [
            'milestone_id', 'learning_path', 'path_name', 'name',
            'description', 'milestone_type', 'requirements', 'points',
            'icon', 'badge_image', 'cultural_reference', 'created_at'
        ]
        read_only_fields = ['milestone_id', 'path_name', 'created_at']


class UserMilestoneSerializer(serializers.ModelSerializer):
    """
    Serializer for user achievements
    """
    milestone_details = MilestoneSerializer(source='milestone', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserMilestone
        fields = [
            'id', 'user', 'user_email', 'milestone', 'milestone_details',
            'learning_path', 'achieved_at', 'achievement_data'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'milestone_details', 'achieved_at'
        ]


class LearningPathCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating personalized learning paths
    """
    class Meta:
        model = LearningPath
        fields = [
            'name', 'description', 'path_type', 'difficulty_level',
            'learning_goal', 'estimated_duration_weeks', 'target_proficiency',
            'focus_areas', 'cultural_context'
        ]

    def validate_focus_areas(self, value):
        """
        Validate focus areas are valid
        """
        valid_areas = [
            'pronunciation', 'grammar', 'vocabulary',
            'fluency', 'listening', 'cultural'
        ]
        if not isinstance(value, list):
            raise serializers.ValidationError("Focus areas must be a list")

        for area in value:
            if area not in valid_areas:
                raise serializers.ValidationError(
                    f"Invalid focus area: {area}. Valid areas: {valid_areas}"
                )

        return value


class PathRecommendationSerializer(serializers.Serializer):
    """
    Serializer for path recommendations based on assessment
    """
    current_level = serializers.ChoiceField(choices=[
        'A1', 'A2', 'B1', 'B2', 'C1', 'C2'
    ])
    target_level = serializers.ChoiceField(choices=[
        'A1', 'A2', 'B1', 'B2', 'C1', 'C2'
    ])
    learning_goals = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    available_hours_per_week = serializers.IntegerField(min_value=1, max_value=40)
    preferred_learning_style = serializers.ChoiceField(
        choices=['visual', 'auditory', 'kinesthetic', 'reading'],
        required=False
    )
    cultural_preferences = serializers.DictField(required=False)
