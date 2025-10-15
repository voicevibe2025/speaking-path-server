"""
Serializers for Analytics app
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    UserAnalytics,
    SessionAnalytics,
    LearningProgress,
    ErrorPattern,
    SkillAssessment,
    ChatModeUsage
)

User = get_user_model()


class UserAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for UserAnalytics model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    improvement_percentage = serializers.SerializerMethodField()
    proficiency_level = serializers.SerializerMethodField()
    practice_consistency = serializers.SerializerMethodField()

    class Meta:
        model = UserAnalytics
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_improvement_percentage(self, obj):
        """Calculate improvement percentage from initial score"""
        if obj.initial_proficiency_score == 0:
            return 0
        improvement = obj.overall_proficiency_score - obj.initial_proficiency_score
        return round((improvement / obj.initial_proficiency_score) * 100, 2)

    def get_proficiency_level(self, obj):
        """Determine proficiency level based on score"""
        score = obj.overall_proficiency_score
        if score >= 90:
            return 'Proficient'
        elif score >= 75:
            return 'Advanced'
        elif score >= 60:
            return 'Upper Intermediate'
        elif score >= 45:
            return 'Intermediate'
        elif score >= 30:
            return 'Elementary'
        else:
            return 'Beginner'

    def get_practice_consistency(self, obj):
        """Calculate practice consistency score"""
        if obj.total_sessions_completed == 0:
            return 0
        # Calculate consistency based on streak and total sessions
        consistency = (obj.current_streak_days / max(obj.total_sessions_completed, 1)) * 100
        return min(round(consistency, 2), 100)


class SessionAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for SessionAnalytics model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    performance_summary = serializers.SerializerMethodField()
    error_summary = serializers.SerializerMethodField()

    class Meta:
        model = SessionAnalytics
        fields = '__all__'
        read_only_fields = ['session_id', 'created_at']

    def get_duration_minutes(self, obj):
        """Convert duration to minutes"""
        return round(obj.duration_seconds / 60, 2)

    def get_performance_summary(self, obj):
        """Create performance summary"""
        return {
            'overall': obj.overall_score,
            'pronunciation': obj.pronunciation_score,
            'fluency': obj.fluency_score,
            'vocabulary': obj.vocabulary_score,
            'grammar': obj.grammar_score,
            'coherence': obj.coherence_score,
            'average': round((
                obj.pronunciation_score +
                obj.fluency_score +
                obj.vocabulary_score +
                obj.grammar_score +
                obj.coherence_score
            ) / 5, 2)
        }

    def get_error_summary(self, obj):
        """Summarize errors"""
        total_errors = (
            obj.pronunciation_errors_count +
            obj.grammar_errors_count +
            obj.vocabulary_errors_count
        )
        return {
            'total': total_errors,
            'pronunciation': obj.pronunciation_errors_count,
            'grammar': obj.grammar_errors_count,
            'vocabulary': obj.vocabulary_errors_count,
            'error_rate': round(total_errors / max(obj.total_words, 1) * 100, 2)
        }


class SessionAnalyticsCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SessionAnalytics"""

    class Meta:
        model = SessionAnalytics
        fields = [
            'session_type', 'scenario_id', 'difficulty_level',
            'start_time', 'end_time', 'duration_seconds',
            'speaking_time_seconds', 'silence_time_seconds',
            'overall_score', 'pronunciation_score', 'fluency_score',
            'vocabulary_score', 'grammar_score', 'coherence_score',
            'total_words', 'unique_words', 'words_per_minute',
            'filler_words_count', 'pronunciation_errors_count',
            'grammar_errors_count', 'vocabulary_errors_count',
            'common_errors', 'pause_count', 'retry_count',
            'hint_requests', 'is_completed', 'completion_percentage'
        ]

    def validate(self, data):
        """Validate session data"""
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError(
                "End time must be after start time"
            )

        # Validate duration
        calculated_duration = (data['end_time'] - data['start_time']).total_seconds()
        if abs(calculated_duration - data['duration_seconds']) > 60:  # 1 minute tolerance
            data['duration_seconds'] = int(calculated_duration)

        return data


class LearningProgressSerializer(serializers.ModelSerializer):
    """Serializer for LearningProgress model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    overall_average_score = serializers.SerializerMethodField()
    goal_completion_rate = serializers.SerializerMethodField()

    class Meta:
        model = LearningProgress
        fields = '__all__'
        read_only_fields = ['progress_id', 'created_at', 'updated_at']

    def get_overall_average_score(self, obj):
        """Calculate overall average score for the day"""
        scores = [
            obj.avg_pronunciation_score,
            obj.avg_fluency_score,
            obj.avg_vocabulary_score,
            obj.avg_grammar_score,
            obj.avg_coherence_score
        ]
        return round(sum(scores) / len(scores), 2)

    def get_goal_completion_rate(self, obj):
        """Calculate goal completion percentage"""
        if obj.daily_goal_minutes == 0:
            return 100
        completion = (obj.practice_time_minutes / obj.daily_goal_minutes) * 100
        return min(round(completion, 2), 100)


class ErrorPatternSerializer(serializers.ModelSerializer):
    """Serializer for ErrorPattern model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    priority_score = serializers.SerializerMethodField()
    improvement_status = serializers.SerializerMethodField()

    class Meta:
        model = ErrorPattern
        fields = '__all__'
        read_only_fields = ['pattern_id', 'created_at', 'updated_at']

    def get_priority_score(self, obj):
        """Calculate priority score for addressing this error"""
        # Higher occurrence, severity, and impact = higher priority
        priority = (
            obj.occurrence_count * 0.4 +
            obj.severity_level * 20 * 0.3 +
            obj.impact_on_communication * 100 * 0.3
        )
        return round(priority, 2)

    def get_improvement_status(self, obj):
        """Determine improvement status"""
        if obj.is_resolved:
            return 'Resolved'
        elif obj.is_improving and obj.improvement_rate > 20:
            return 'Improving Well'
        elif obj.is_improving:
            return 'Slowly Improving'
        else:
            return 'Needs Attention'


class SkillAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for SkillAssessment model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    overall_score_calculated = serializers.SerializerMethodField()
    skill_breakdown = serializers.SerializerMethodField()
    improvement_areas = serializers.SerializerMethodField()

    class Meta:
        model = SkillAssessment
        fields = '__all__'
        read_only_fields = ['assessment_id', 'created_at']

    def get_overall_score_calculated(self, obj):
        """Get calculated overall score"""
        return obj.calculate_overall_score()

    def get_skill_breakdown(self, obj):
        """Create skill breakdown with levels"""
        def get_level(score):
            if score >= 80:
                return 'Excellent'
            elif score >= 60:
                return 'Good'
            elif score >= 40:
                return 'Fair'
            else:
                return 'Needs Improvement'

        return {
            'pronunciation': {
                'score': obj.pronunciation_score,
                'level': get_level(obj.pronunciation_score)
            },
            'fluency': {
                'score': obj.fluency_score,
                'level': get_level(obj.fluency_score)
            },
            'vocabulary': {
                'score': obj.vocabulary_score,
                'level': get_level(obj.vocabulary_score)
            },
            'grammar': {
                'score': obj.grammar_score,
                'level': get_level(obj.grammar_score)
            },
            'coherence': {
                'score': obj.coherence_score,
                'level': get_level(obj.coherence_score)
            },
            'cultural_appropriateness': {
                'score': obj.cultural_appropriateness_score,
                'level': get_level(obj.cultural_appropriateness_score)
            }
        }

    def get_improvement_areas(self, obj):
        """Identify top areas for improvement"""
        skills = {
            'pronunciation': obj.pronunciation_score,
            'fluency': obj.fluency_score,
            'vocabulary': obj.vocabulary_score,
            'grammar': obj.grammar_score,
            'coherence': obj.coherence_score,
            'cultural_appropriateness': obj.cultural_appropriateness_score
        }

        # Sort by score (lowest first)
        sorted_skills = sorted(skills.items(), key=lambda x: x[1])

        # Return bottom 3 skills as improvement areas
        return [skill[0] for skill in sorted_skills[:3]]


class ProgressSummarySerializer(serializers.Serializer):
    """Serializer for progress summary dashboard"""
    period = serializers.CharField()  # 'daily', 'weekly', 'monthly'
    total_practice_time = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    average_score = serializers.FloatField()
    improvement_rate = serializers.FloatField()
    streak_days = serializers.IntegerField()
    achievements_earned = serializers.IntegerField()
    top_skills = serializers.ListField(child=serializers.CharField())
    areas_to_improve = serializers.ListField(child=serializers.CharField())

    def to_representation(self, instance):
        """Custom representation for progress summary"""
        data = super().to_representation(instance)

        # Add performance trend
        if instance.get('previous_average_score'):
            current = instance['average_score']
            previous = instance['previous_average_score']
            data['trend'] = 'improving' if current > previous else 'declining'
            data['trend_percentage'] = round(
                ((current - previous) / previous) * 100, 2
            ) if previous > 0 else 0

        return data


class AnalyticsDashboardSerializer(serializers.Serializer):
    """Serializer for analytics dashboard"""
    user_analytics = UserAnalyticsSerializer()
    recent_sessions = SessionAnalyticsSerializer(many=True)
    weekly_progress = LearningProgressSerializer(many=True)
    active_error_patterns = ErrorPatternSerializer(many=True)
    latest_assessment = SkillAssessmentSerializer()
    progress_summary = ProgressSummarySerializer()

    def to_representation(self, instance):
        """Custom representation for dashboard"""
        data = super().to_representation(instance)

        # Add insights
        data['insights'] = self.generate_insights(instance)

        return data

    def generate_insights(self, data):
        """Generate personalized insights"""
        insights = []

        # Check streak
        if data.get('user_analytics'):
            streak = data['user_analytics'].current_streak_days
            if streak > 7:
                insights.append({
                    'type': 'achievement',
                    'message': f'Great job! You\'re on a {streak}-day streak!'
                })
            elif streak == 0:
                insights.append({
                    'type': 'motivation',
                    'message': 'Start practicing today to build your streak!'
                })

        # Check improvement
        if data.get('progress_summary'):
            if data['progress_summary']['improvement_rate'] > 5:
                insights.append({
                    'type': 'progress',
                    'message': 'Excellent progress! You\'re improving rapidly.'
                })

        # Check error patterns
        if data.get('active_error_patterns'):
            if len(data['active_error_patterns']) > 0:
                insights.append({
                    'type': 'focus',
                    'message': f'Focus on {data["active_error_patterns"][0].error_type} to boost your score.'
                })

        return insights


class ChatModeUsageSerializer(serializers.ModelSerializer):
    """Serializer for ChatModeUsage model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    display_name = serializers.CharField(source='user.display_name', read_only=True)
    current_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatModeUsage
        fields = [
            'usage_id', 'user', 'user_id', 'user_email', 'username', 'display_name',
            'mode', 'session_id', 'started_at', 'ended_at', 'duration_seconds',
            'current_duration', 'message_count', 'is_active', 'device_info',
            'app_version', 'created_at', 'updated_at'
        ]
        read_only_fields = ['usage_id', 'session_id', 'created_at', 'updated_at']
    
    def get_current_duration(self, obj):
        """Get current duration in seconds"""
        return int(obj.calculate_duration())


class ChatModeUsageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ChatModeUsage sessions"""
    
    class Meta:
        model = ChatModeUsage
        fields = ['mode', 'device_info', 'app_version']
    
    def validate_mode(self, value):
        """Validate mode is either 'text' or 'voice'"""
        if value not in ['text', 'voice']:
            raise serializers.ValidationError(
                "Mode must be either 'text' or 'voice'"
            )
        return value


class ChatModeStatsSerializer(serializers.Serializer):
    """Serializer for chat mode usage statistics"""
    total_sessions = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    text_chat_sessions = serializers.IntegerField()
    voice_chat_sessions = serializers.IntegerField()
    text_chat_percentage = serializers.FloatField()
    voice_chat_percentage = serializers.FloatField()
    average_session_duration = serializers.FloatField()
    total_messages = serializers.IntegerField()
    unique_users = serializers.IntegerField()
    active_users_now = serializers.IntegerField()
    
    # Per-mode breakdown
    text_mode_stats = serializers.DictField(child=serializers.FloatField())
    voice_mode_stats = serializers.DictField(child=serializers.FloatField())
    
    # Time-based stats
    today_sessions = serializers.IntegerField()
    this_week_sessions = serializers.IntegerField()
    this_month_sessions = serializers.IntegerField()


class ChatModeUserStatsSerializer(serializers.Serializer):
    """Serializer for individual user chat mode statistics"""
    user_id = serializers.IntegerField()
    user_email = serializers.EmailField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    total_sessions = serializers.IntegerField()
    text_chat_count = serializers.IntegerField()
    voice_chat_count = serializers.IntegerField()
    preferred_mode = serializers.CharField()
    total_duration_seconds = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    last_session_at = serializers.DateTimeField()
    is_currently_active = serializers.BooleanField()
