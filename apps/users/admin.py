"""
Admin configuration for user profile models
"""
from django.contrib import admin
from .models import UserProfile, LearningPreference, UserAchievement


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin for UserProfile model
    """
    list_display = (
        'user', 'current_proficiency', 'learning_goal',
        'native_language', 'streak_days', 'total_practice_time',
        'last_practice_date', 'created_at'
    )
    list_filter = (
        'current_proficiency', 'learning_goal',
        'native_language', 'target_language',
        'preferred_reward_type', 'enable_notifications'
    )
    search_fields = ('user__email', 'user__username', 'phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'phone_number', 'avatar_url', 'bio')
        }),
        ('Language Settings', {
            'fields': (
                'native_language', 'target_language',
                'current_proficiency', 'learning_goal'
            )
        }),
        ('Learning Preferences', {
            'fields': (
                'daily_practice_goal', 'preferred_session_duration'
            )
        }),
        ('Cultural Preferences', {
            'fields': (
                'power_distance_preference', 'individualism_preference',
                'masculinity_preference', 'uncertainty_avoidance_preference',
                'long_term_orientation_preference'
            ),
            'classes': ('collapse',)
        }),
        ('Gamification', {
            'fields': (
                'preferred_reward_type', 'enable_notifications',
                'enable_reminders'
            )
        }),
        ('Statistics', {
            'fields': (
                'total_practice_time', 'streak_days',
                'last_practice_date'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(LearningPreference)
class LearningPreferenceAdmin(admin.ModelAdmin):
    """
    Admin for LearningPreference model
    """
    list_display = (
        'user', 'ai_personality', 'immediate_correction',
        'detailed_feedback', 'cultural_context', 'created_at'
    )
    list_filter = (
        'ai_personality', 'immediate_correction',
        'detailed_feedback', 'cultural_context'
    )
    search_fields = ('user__email', 'user__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Scenario Preferences', {
            'fields': ('preferred_scenarios', 'avoided_topics')
        }),
        ('Learning Style', {
            'fields': (
                'visual_learning', 'auditory_learning',
                'kinesthetic_learning'
            )
        }),
        ('Feedback Preferences', {
            'fields': (
                'immediate_correction', 'detailed_feedback',
                'cultural_context'
            )
        }),
        ('AI Settings', {
            'fields': (
                'ai_personality', 'difficulty_adaptation_speed'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """
    Admin for UserAchievement model
    """
    list_display = (
        'user', 'achievement_name', 'category',
        'is_completed', 'points_earned', 'earned_at'
    )
    list_filter = (
        'category', 'is_completed', 'earned_at'
    )
    search_fields = (
        'user__email', 'user__username',
        'achievement_name', 'achievement_type'
    )
    ordering = ('-earned_at', '-created_at')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Achievement Details', {
            'fields': (
                'achievement_type', 'achievement_name',
                'achievement_description', 'category'
            )
        }),
        ('Progress', {
            'fields': (
                'progress_current', 'progress_target',
                'is_completed'
            )
        }),
        ('Rewards', {
            'fields': (
                'points_earned', 'badge_image_url'
            )
        }),
        ('Timestamps', {
            'fields': ('earned_at', 'created_at'),
            'classes': ('collapse',)
        })
    )

    def get_readonly_fields(self, request, obj=None):
        """Make achievement_type readonly after creation"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('achievement_type',)
        return self.readonly_fields
