"""
Admin configuration for user profile models
"""
from django.contrib import admin
from .models import UserProfile, LearningPreference, UserAchievement, UserBlock, Report, PrivacySettings


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


@admin.register(PrivacySettings)
class PrivacySettingsAdmin(admin.ModelAdmin):
    """
    Admin for PrivacySettings model
    """
    list_display = ('user', 'hide_avatar', 'hide_online_status', 'allow_messages_from_strangers', 'updated_at')
    list_filter = ('hide_avatar', 'hide_online_status', 'allow_messages_from_strangers')
    search_fields = ('user__email', 'user__username')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    """
    Admin for UserBlock model
    """
    list_display = ('blocker', 'blocked_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('blocker__email', 'blocker__username', 'blocked_user__email', 'blocked_user__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Admin for Report model with moderation capabilities
    """
    list_display = ('id', 'report_type', 'reason', 'reporter', 'status', 'created_at')
    list_filter = ('report_type', 'reason', 'status', 'created_at')
    search_fields = ('reporter__email', 'reporter__username', 'reported_user__email', 'reported_user__username', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('reporter', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'report_type', 'reason', 'description')
        }),
        ('Reported Entity', {
            'fields': ('reported_user', 'reported_post_id', 'reported_comment_id')
        }),
        ('Moderation', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'moderator_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_reviewing', 'mark_as_resolved', 'mark_as_dismissed']
    
    def mark_as_reviewing(self, request, queryset):
        queryset.update(status='reviewing', reviewed_by=request.user)
        self.message_user(request, f"{queryset.count()} report(s) marked as under review.")
    mark_as_reviewing.short_description = "Mark selected reports as under review"
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} report(s) marked as resolved.")
    mark_as_resolved.short_description = "Mark selected reports as resolved"
    
    def mark_as_dismissed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='dismissed', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} report(s) marked as dismissed.")
    mark_as_dismissed.short_description = "Mark selected reports as dismissed"
