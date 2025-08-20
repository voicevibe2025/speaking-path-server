"""
Admin configuration for Learning Paths
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    LearningPath,
    LearningModule,
    ModuleActivity,
    UserProgress,
    Milestone,
    UserMilestone
)


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    """
    Admin interface for Learning Paths
    """
    list_display = [
        'path_id_short', 'user', 'name', 'path_type',
        'difficulty_level', 'is_active', 'progress_display',
        'created_at'
    ]
    list_filter = [
        'path_type', 'difficulty_level', 'is_active',
        'target_proficiency', 'created_at'
    ]
    search_fields = ['name', 'user__email', 'path_id', 'description']
    ordering = ['-created_at']

    readonly_fields = [
        'path_id', 'created_at', 'started_at',
        'completed_at', 'last_accessed'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('path_id', 'user', 'name', 'description')
        }),
        ('Path Configuration', {
            'fields': (
                'path_type', 'difficulty_level', 'target_proficiency',
                'learning_goal', 'estimated_duration_weeks'
            )
        }),
        ('Progress & Status', {
            'fields': (
                'is_active', 'progress_percentage', 'current_module_index',
                'started_at', 'completed_at', 'last_accessed'
            )
        }),
        ('Personalization', {
            'fields': ('focus_areas', 'cultural_context'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def path_id_short(self, obj):
        """Display shortened UUID"""
        return str(obj.path_id)[:8] + '...'
    path_id_short.short_description = 'Path ID'

    def progress_display(self, obj):
        """Display progress with color coding"""
        color = 'green' if obj.progress_percentage >= 70 else 'orange' if obj.progress_percentage >= 30 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            obj.progress_percentage
        )
    progress_display.short_description = 'Progress'


class ModuleActivityInline(admin.TabularInline):
    """
    Inline admin for activities within modules
    """
    model = ModuleActivity
    extra = 0
    fields = [
        'name', 'activity_type', 'order_index',
        'estimated_duration_minutes', 'points', 'requires_ai_evaluation'
    ]
    ordering = ['order_index']


@admin.register(LearningModule)
class LearningModuleAdmin(admin.ModelAdmin):
    """
    Admin interface for Learning Modules
    """
    list_display = [
        'module_id_short', 'learning_path', 'name', 'module_type',
        'order_index', 'is_locked', 'is_completed', 'completion_display'
    ]
    list_filter = [
        'module_type', 'is_locked', 'is_completed',
        'created_at'
    ]
    search_fields = ['name', 'module_id', 'learning_path__name']
    ordering = ['learning_path', 'order_index']

    readonly_fields = [
        'module_id', 'created_at', 'unlocked_at',
        'started_at', 'completed_at'
    ]

    inlines = [ModuleActivityInline]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'module_id', 'learning_path', 'name',
                'description', 'module_type', 'order_index'
            )
        }),
        ('Content & Requirements', {
            'fields': (
                'learning_objectives', 'prerequisites', 'content',
                'estimated_duration_minutes', 'minimum_score', 'max_attempts'
            )
        }),
        ('Progress & Status', {
            'fields': (
                'is_locked', 'is_completed', 'completion_percentage',
                'unlocked_at', 'started_at', 'completed_at'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def module_id_short(self, obj):
        """Display shortened UUID"""
        return str(obj.module_id)[:8] + '...'
    module_id_short.short_description = 'Module ID'

    def completion_display(self, obj):
        """Display completion percentage with color"""
        color = 'green' if obj.completion_percentage >= 70 else 'orange' if obj.completion_percentage >= 30 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            obj.completion_percentage
        )
    completion_display.short_description = 'Completion'


@admin.register(ModuleActivity)
class ModuleActivityAdmin(admin.ModelAdmin):
    """
    Admin interface for Module Activities
    """
    list_display = [
        'activity_id_short', 'module', 'name', 'activity_type',
        'order_index', 'points', 'requires_ai_evaluation'
    ]
    list_filter = [
        'activity_type', 'requires_ai_evaluation',
        'created_at'
    ]
    search_fields = ['name', 'activity_id', 'module__name']
    ordering = ['module', 'order_index']

    readonly_fields = ['activity_id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'activity_id', 'module', 'name',
                'description', 'activity_type', 'order_index'
            )
        }),
        ('Content', {
            'fields': (
                'instructions', 'content', 'resources',
                'estimated_duration_minutes', 'points', 'passing_score'
            )
        }),
        ('AI Integration', {
            'fields': (
                'requires_ai_evaluation', 'ai_evaluation_criteria'
            )
        }),
        ('Cultural Adaptation', {
            'fields': ('cultural_notes', 'indonesian_context'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def activity_id_short(self, obj):
        """Display shortened UUID"""
        return str(obj.activity_id)[:8] + '...'
    activity_id_short.short_description = 'Activity ID'


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    """
    Admin interface for User Progress
    """
    list_display = [
        'user', 'learning_path', 'module', 'activity',
        'status', 'score_display', 'attempts', 'last_attempt_at'
    ]
    list_filter = [
        'status', 'started_at', 'completed_at'
    ]
    search_fields = [
        'user__email', 'learning_path__name',
        'module__name', 'activity__name'
    ]
    ordering = ['-last_attempt_at']

    readonly_fields = [
        'started_at', 'completed_at', 'last_attempt_at'
    ]

    fieldsets = (
        ('User & Path Information', {
            'fields': (
                'user', 'learning_path', 'module', 'activity'
            )
        }),
        ('Progress & Performance', {
            'fields': (
                'status', 'score', 'attempts', 'time_spent_minutes'
            )
        }),
        ('Results & Feedback', {
            'fields': ('results', 'ai_feedback'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'started_at', 'completed_at', 'last_attempt_at'
            ),
            'classes': ('collapse',)
        })
    )

    def score_display(self, obj):
        """Display score with color coding"""
        if obj.score is None:
            return '-'
        color = 'green' if obj.score >= 70 else 'orange' if obj.score >= 50 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            obj.score
        )
    score_display.short_description = 'Score'


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    """
    Admin interface for Milestones
    """
    list_display = [
        'milestone_id_short', 'name', 'milestone_type',
        'learning_path', 'points', 'cultural_reference'
    ]
    list_filter = ['milestone_type', 'created_at']
    search_fields = ['name', 'milestone_id', 'description']
    ordering = ['learning_path', 'name']

    readonly_fields = ['milestone_id', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'milestone_id', 'learning_path', 'name',
                'description', 'milestone_type'
            )
        }),
        ('Requirements & Rewards', {
            'fields': ('requirements', 'points')
        }),
        ('Visual Elements', {
            'fields': ('icon', 'badge_image', 'cultural_reference')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def milestone_id_short(self, obj):
        """Display shortened UUID"""
        return str(obj.milestone_id)[:8] + '...'
    milestone_id_short.short_description = 'Milestone ID'


@admin.register(UserMilestone)
class UserMilestoneAdmin(admin.ModelAdmin):
    """
    Admin interface for User Achievements
    """
    list_display = [
        'user', 'milestone', 'learning_path', 'achieved_at'
    ]
    list_filter = ['achieved_at']
    search_fields = [
        'user__email', 'milestone__name',
        'learning_path__name'
    ]
    ordering = ['-achieved_at']

    readonly_fields = ['achieved_at']

    fieldsets = (
        ('Achievement Information', {
            'fields': (
                'user', 'milestone', 'learning_path',
                'achieved_at'
            )
        }),
        ('Achievement Data', {
            'fields': ('achievement_data',),
            'classes': ('collapse',)
        })
    )
