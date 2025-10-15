"""
Admin configuration for Analytics app
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    UserAnalytics,
    SessionAnalytics,
    LearningProgress,
    ErrorPattern,
    SkillAssessment,
    ChatModeUsage
)


@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    """Admin for UserAnalytics"""
    list_display = [
        'user',
        'display_proficiency_level',
        'display_overall_score',
        'display_streak',
        'total_sessions_completed',
        'display_practice_time',
        'display_improvement',
        'last_practice_date'
    ]
    list_filter = [
        'last_practice_date',
        ('overall_proficiency_score', admin.EmptyFieldListFilter),
    ]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'created_at',
        'updated_at',
        'display_skill_radar',
        'display_progress_chart',
        'display_achievement_badges'
    ]

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Overall Performance', {
            'fields': (
                'overall_proficiency_score',
                'initial_proficiency_score',
                'proficiency_level',
                'improvement_rate',
                'display_progress_chart'
            )
        }),
        ('Skill Scores', {
            'fields': (
                'pronunciation_score',
                'fluency_score',
                'vocabulary_score',
                'grammar_score',
                'coherence_score',
                'display_skill_radar'
            ),
            'classes': ('collapse',)
        }),
        ('Practice Statistics', {
            'fields': (
                'total_sessions_completed',
                'total_practice_time_minutes',
                'average_session_duration_minutes',
                'current_streak_days',
                'longest_streak_days',
                'last_practice_date'
            )
        }),
        ('Achievements', {
            'fields': (
                'achievements_earned',
                'total_xp_earned',
                'display_achievement_badges'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def display_proficiency_level(self, obj):
        """Display proficiency level with color"""
        colors = {
            'beginner': '#ff6b6b',
            'elementary': '#feca57',
            'intermediate': '#48dbfb',
            'upper_intermediate': '#0abde3',
            'advanced': '#00d2d3',
            'proficient': '#54a0ff',
            'native_like': '#5f27cd'
        }
        color = colors.get(obj.proficiency_level, '#95afc0')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_proficiency_level_display()
        )
    display_proficiency_level.short_description = 'Level'

    def display_overall_score(self, obj):
        """Display overall score with progress bar"""
        score = obj.overall_proficiency_score or 0
        color = '#28a745' if score >= 70 else '#ffc107' if score >= 50 else '#dc3545'
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; color: white; '
            'text-align: center; border-radius: 3px; padding: 2px;">{:.1f}%</div></div>',
            score, color, score
        )
    display_overall_score.short_description = 'Score'

    def display_streak(self, obj):
        """Display current streak with fire emoji"""
        if obj.current_streak_days >= 7:
            emoji = '🔥🔥🔥'
        elif obj.current_streak_days >= 3:
            emoji = '🔥🔥'
        elif obj.current_streak_days >= 1:
            emoji = '🔥'
        else:
            emoji = '❄️'

        return format_html(
            '{} <strong>{}</strong> days (best: {})',
            emoji, obj.current_streak_days, obj.longest_streak_days
        )
    display_streak.short_description = 'Streak'

    def display_practice_time(self, obj):
        """Display total practice time in hours"""
        hours = obj.total_practice_time_minutes / 60
        return format_html(
            '<strong>{:.1f}</strong> hours',
            hours
        )
    display_practice_time.short_description = 'Total Time'

    def display_improvement(self, obj):
        """Display improvement rate with arrow"""
        rate = obj.improvement_rate or 0
        if rate > 0:
            arrow = '↑'
            color = '#28a745'
        elif rate < 0:
            arrow = '↓'
            color = '#dc3545'
        else:
            arrow = '→'
            color = '#6c757d'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {:.1f}%</span>',
            color, arrow, abs(rate)
        )
    display_improvement.short_description = 'Improvement'

    def display_skill_radar(self, obj):
        """Display skill scores as a radar chart visualization"""
        return format_html(
            '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">'
            '<strong>Skills Overview:</strong><br>'
            '🎯 Pronunciation: {:.1f}%<br>'
            '💬 Fluency: {:.1f}%<br>'
            '📚 Vocabulary: {:.1f}%<br>'
            '✏️ Grammar: {:.1f}%<br>'
            '🔗 Coherence: {:.1f}%'
            '</div>',
            obj.pronunciation_score or 0,
            obj.fluency_score or 0,
            obj.vocabulary_score or 0,
            obj.grammar_score or 0,
            obj.coherence_score or 0
        )
    display_skill_radar.short_description = 'Skill Breakdown'

    def display_progress_chart(self, obj):
        """Display progress visualization"""
        initial = obj.initial_proficiency_score or 0
        current = obj.overall_proficiency_score or 0
        improvement = current - initial

        return format_html(
            '<div style="padding: 10px; background: linear-gradient(to right, #667eea, #764ba2); '
            'color: white; border-radius: 5px;">'
            '<strong>Progress Journey:</strong><br>'
            'Started at: {:.1f}% → Now: {:.1f}%<br>'
            'Total Gain: <strong>{:+.1f}%</strong>'
            '</div>',
            initial, current, improvement
        )
    display_progress_chart.short_description = 'Progress Journey'

    def display_achievement_badges(self, obj):
        """Display achievements as badges"""
        achievements = obj.achievements_earned or 0
        xp = obj.total_xp_earned or 0

        badges = ''
        if achievements >= 50:
            badges += '🏆'
        if achievements >= 25:
            badges += '🥇'
        if achievements >= 10:
            badges += '🥈'
        if achievements >= 5:
            badges += '🥉'

        return format_html(
            '<div>{} <strong>{}</strong> achievements | <strong>{}</strong> XP</div>',
            badges, achievements, xp
        )
    display_achievement_badges.short_description = 'Achievements'


@admin.register(SessionAnalytics)
class SessionAnalyticsAdmin(admin.ModelAdmin):
    """Admin for SessionAnalytics"""
    list_display = [
        'session_id',
        'user',
        'session_type',
        'display_overall_score',
        'display_duration',
        'total_words',
        'display_skill_scores',
        'created_at'
    ]
    list_filter = [
        'session_type',
        'created_at',
        ('overall_score', admin.EmptyFieldListFilter),
    ]
    search_fields = ['session_id', 'user__username', 'user__email', 'topic']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'session_id',
        'created_at',
        'display_detailed_feedback',
        'display_error_analysis'
    ]

    fieldsets = (
        ('Session Information', {
            'fields': (
                'session_id',
                'user',
                'session_type',
                'topic',
                'difficulty_level'
            )
        }),
        ('Performance Scores', {
            'fields': (
                'overall_score',
                'pronunciation_score',
                'fluency_score',
                'vocabulary_score',
                'grammar_score',
                'coherence_score',
                'display_detailed_feedback'
            )
        }),
        ('Session Statistics', {
            'fields': (
                'duration_seconds',
                'total_words',
                'unique_words',
                'filler_words_count',
                'pause_count',
                'average_pause_duration'
            )
        }),
        ('Errors and Feedback', {
            'fields': (
                'error_count',
                'error_types',
                'ai_feedback',
                'display_error_analysis'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def display_overall_score(self, obj):
        """Display overall score with grade"""
        score = obj.overall_score or 0
        if score >= 90:
            grade = 'A+'
            color = '#28a745'
        elif score >= 80:
            grade = 'A'
            color = '#28a745'
        elif score >= 70:
            grade = 'B'
            color = '#17a2b8'
        elif score >= 60:
            grade = 'C'
            color = '#ffc107'
        else:
            grade = 'D'
            color = '#dc3545'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{} ({:.1f})</span>',
            color, grade, score
        )
    display_overall_score.short_description = 'Score'
    display_overall_score.admin_order_field = 'overall_score'

    def display_duration(self, obj):
        """Display session duration in minutes"""
        minutes = obj.duration_seconds / 60
        return format_html(
            '<strong>{:.1f}</strong> min',
            minutes
        )
    display_duration.short_description = 'Duration'
    display_duration.admin_order_field = 'duration_seconds'

    def display_skill_scores(self, obj):
        """Display skill scores as mini bars"""
        skills = [
            ('P', obj.pronunciation_score),
            ('F', obj.fluency_score),
            ('V', obj.vocabulary_score),
            ('G', obj.grammar_score),
            ('C', obj.coherence_score)
        ]

        bars = []
        for label, score in skills:
            score = score or 0
            color = '#28a745' if score >= 70 else '#ffc107' if score >= 50 else '#dc3545'
            bars.append(format_html(
                '<span title="{}: {:.0f}%" style="display: inline-block; width: 30px; '
                'background: linear-gradient(to right, {} {}%, #e9ecef {}%); '
                'text-align: center; margin: 0 2px; border-radius: 2px; font-size: 11px;">{}</span>',
                label, score, color, score, score, label
            ))

        return format_html(''.join(bars))
    display_skill_scores.short_description = 'Skills'

    def display_detailed_feedback(self, obj):
        """Display detailed feedback summary"""
        return format_html(
            '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">'
            '<strong>Session Summary:</strong><br>'
            '📝 Words: {} total, {} unique<br>'
            '⏸️ Pauses: {} (avg {:.1f}s)<br>'
            '❌ Errors: {} total<br>'
            '💭 Filler words: {}'
            '</div>',
            obj.total_words,
            obj.unique_words,
            obj.pause_count,
            obj.average_pause_duration or 0,
            obj.error_count,
            obj.filler_words_count
        )
    display_detailed_feedback.short_description = 'Session Details'

    def display_error_analysis(self, obj):
        """Display error type breakdown"""
        if not obj.error_types:
            return 'No errors recorded'

        error_html = '<div style="padding: 10px; background: #fff3cd; border-radius: 5px;">'
        error_html += '<strong>Error Breakdown:</strong><br>'

        for error_type, count in (obj.error_types or {}).items():
            error_html += f'• {error_type}: {count}<br>'

        error_html += '</div>'
        return format_html(error_html)
    display_error_analysis.short_description = 'Error Analysis'


@admin.register(LearningProgress)
class LearningProgressAdmin(admin.ModelAdmin):
    """Admin for LearningProgress"""
    list_display = [
        'user',
        'date',
        'display_practice_time',
        'sessions_count',
        'words_practiced',
        'display_goal_achievement',
        'display_avg_scores'
    ]
    list_filter = [
        'goal_achieved',
        'date',
        'week_number',
        'month'
    ]
    search_fields = ['user__username', 'user__email']
    date_hierarchy = 'date'
    readonly_fields = ['progress_id', 'week_number', 'month', 'year']

    fieldsets = (
        ('Progress Information', {
            'fields': (
                'progress_id',
                'user',
                'date',
                'week_number',
                'month',
                'year'
            )
        }),
        ('Daily Statistics', {
            'fields': (
                'practice_time_minutes',
                'sessions_count',
                'words_practiced',
                'daily_goal_minutes',
                'goal_achieved'
            )
        }),
        ('Average Scores', {
            'fields': (
                'avg_pronunciation_score',
                'avg_fluency_score',
                'avg_vocabulary_score',
                'avg_grammar_score',
                'avg_coherence_score'
            ),
            'classes': ('collapse',)
        })
    )

    def display_practice_time(self, obj):
        """Display practice time with progress bar"""
        time = obj.practice_time_minutes
        goal = obj.daily_goal_minutes
        percentage = min((time / goal * 100) if goal > 0 else 0, 100)

        color = '#28a745' if percentage >= 100 else '#ffc107' if percentage >= 50 else '#dc3545'

        return format_html(
            '<div style="width: 150px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; color: white; '
            'text-align: center; border-radius: 3px; padding: 2px;">{}/{} min</div></div>',
            percentage, color, int(time), goal
        )
    display_practice_time.short_description = 'Practice Time'

    def display_goal_achievement(self, obj):
        """Display goal achievement status"""
        if obj.goal_achieved:
            return format_html(
                '<span style="color: #28a745; font-size: 20px;">✅</span> Achieved!'
            )
        else:
            percentage = (obj.practice_time_minutes / obj.daily_goal_minutes * 100) if obj.daily_goal_minutes > 0 else 0
            return format_html(
                '<span style="color: #dc3545;">{:.0f}% of goal</span>',
                percentage
            )
    display_goal_achievement.short_description = 'Goal Status'

    def display_avg_scores(self, obj):
        """Display average scores as compact view"""
        avg_score = (
            (obj.avg_pronunciation_score or 0) +
            (obj.avg_fluency_score or 0) +
            (obj.avg_vocabulary_score or 0) +
            (obj.avg_grammar_score or 0) +
            (obj.avg_coherence_score or 0)
        ) / 5

        color = '#28a745' if avg_score >= 70 else '#ffc107' if avg_score >= 50 else '#dc3545'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{:.1f}%</span>',
            color, avg_score
        )
    display_avg_scores.short_description = 'Avg Score'


@admin.register(ErrorPattern)
class ErrorPatternAdmin(admin.ModelAdmin):
    """Admin for ErrorPattern"""
    list_display = [
        'error_pattern',
        'user',
        'error_type',
        'display_severity',
        'occurrence_count',
        'display_impact',
        'display_resolution_status',
        'last_occurrence'
    ]
    list_filter = [
        'error_type',
        'severity_level',
        'is_resolved',
        'last_occurrence'
    ]
    search_fields = ['user__username', 'error_pattern', 'example_context']
    readonly_fields = [
        'pattern_id',
        'resolved_date',
        'display_examples',
        'display_improvement_tips'
    ]

    fieldsets = (
        ('Error Information', {
            'fields': (
                'pattern_id',
                'user',
                'error_pattern',
                'error_type',
                'severity_level',
                'impact_on_communication'
            )
        }),
        ('Occurrence Details', {
            'fields': (
                'occurrence_count',
                'last_occurrence',
                'example_errors',
                'example_context',
                'display_examples'
            )
        }),
        ('Resolution', {
            'fields': (
                'is_resolved',
                'resolved_date',
                'improvement_suggestions',
                'display_improvement_tips'
            ),
            'classes': ('collapse',)
        })
    )

    actions = ['mark_as_resolved', 'mark_as_unresolved']

    def display_severity(self, obj):
        """Display severity level with color coding"""
        colors = {
            1: ('#28a745', 'Low'),
            2: ('#17a2b8', 'Medium-Low'),
            3: ('#ffc107', 'Medium'),
            4: ('#fd7e14', 'Medium-High'),
            5: ('#dc3545', 'High')
        }
        color, label = colors.get(obj.severity_level, ('#6c757d', 'Unknown'))

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, label
        )
    display_severity.short_description = 'Severity'

    def display_impact(self, obj):
        """Display communication impact"""
        impact = obj.impact_on_communication
        if impact >= 0.7:
            emoji = '🔴'
            label = 'High'
        elif impact >= 0.4:
            emoji = '🟡'
            label = 'Medium'
        else:
            emoji = '🟢'
            label = 'Low'

        return format_html(
            '{} {} ({:.0f}%)',
            emoji, label, impact * 100
        )
    display_impact.short_description = 'Impact'

    def display_resolution_status(self, obj):
        """Display resolution status"""
        if obj.is_resolved:
            days_ago = (timezone.now() - obj.resolved_date).days if obj.resolved_date else 0
            return format_html(
                '<span style="color: #28a745;">✅ Resolved ({} days ago)</span>',
                days_ago
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">⚠️ Active</span>'
            )
    display_resolution_status.short_description = 'Status'

    def display_examples(self, obj):
        """Display example errors"""
        if not obj.example_errors:
            return 'No examples'

        examples_html = '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">'
        examples_html += '<strong>Example Errors:</strong><br>'

        for i, example in enumerate(obj.example_errors[:3], 1):
            examples_html += f'{i}. "{example}"<br>'

        if obj.example_context:
            examples_html += f'<br><em>Context: "{obj.example_context[:100]}..."</em>'

        examples_html += '</div>'
        return format_html(examples_html)
    display_examples.short_description = 'Examples'

    def display_improvement_tips(self, obj):
        """Display improvement suggestions"""
        if not obj.improvement_suggestions:
            return 'No suggestions available'

        tips_html = '<div style="padding: 10px; background: #d1ecf1; border-radius: 5px;">'
        tips_html += '<strong>💡 Improvement Tips:</strong><br>'

        for i, tip in enumerate(obj.improvement_suggestions[:3], 1):
            tips_html += f'{i}. {tip}<br>'

        tips_html += '</div>'
        return format_html(tips_html)
    display_improvement_tips.short_description = 'Improvement Tips'

    def mark_as_resolved(self, request, queryset):
        """Action to mark errors as resolved"""
        updated = queryset.update(
            is_resolved=True,
            resolved_date=timezone.now()
        )
        self.message_user(request, f'{updated} error patterns marked as resolved.')
    mark_as_resolved.short_description = 'Mark selected as resolved'

    def mark_as_unresolved(self, request, queryset):
        """Action to mark errors as unresolved"""
        updated = queryset.update(
            is_resolved=False,
            resolved_date=None
        )
        self.message_user(request, f'{updated} error patterns marked as unresolved.')
    mark_as_unresolved.short_description = 'Mark selected as unresolved'


@admin.register(SkillAssessment)
class SkillAssessmentAdmin(admin.ModelAdmin):
    """Admin for SkillAssessment"""
    list_display = [
        'assessment_id',
        'user',
        'assessment_type',
        'display_overall_score',
        'display_proficiency',
        'display_improvement',
        'assessment_date'
    ]
    list_filter = [
        'assessment_type',
        'proficiency_level',
        'assessment_date'
    ]
    search_fields = ['assessment_id', 'user__username', 'user__email']
    date_hierarchy = 'assessment_date'
    readonly_fields = [
        'assessment_id',
        'created_at',
        'display_skill_breakdown',
        'display_strengths_weaknesses',
        'display_recommendations'
    ]

    fieldsets = (
        ('Assessment Information', {
            'fields': (
                'assessment_id',
                'user',
                'assessment_type',
                'assessment_date'
            )
        }),
        ('Overall Performance', {
            'fields': (
                'overall_score',
                'proficiency_level',
                'improvement_from_last',
                'display_skill_breakdown'
            )
        }),
        ('Skill Scores', {
            'fields': (
                'pronunciation_score',
                'fluency_score',
                'vocabulary_score',
                'grammar_score',
                'coherence_score'
            ),
            'classes': ('collapse',)
        }),
        ('Analysis', {
            'fields': (
                'strengths',
                'weaknesses',
                'recommendations',
                'display_strengths_weaknesses',
                'display_recommendations'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def display_overall_score(self, obj):
        """Display overall score with medal"""
        score = obj.overall_score
        if score >= 90:
            medal = '🥇'
        elif score >= 75:
            medal = '🥈'
        elif score >= 60:
            medal = '🥉'
        else:
            medal = '📊'

        return format_html(
            '{} <strong>{:.1f}%</strong>',
            medal, score
        )
    display_overall_score.short_description = 'Score'
    display_overall_score.admin_order_field = 'overall_score'

    def display_proficiency(self, obj):
        """Display proficiency level with color"""
        colors = {
            'A1': '#ff6b6b',
            'A2': '#feca57',
            'B1': '#48dbfb',
            'B2': '#0abde3',
            'C1': '#00d2d3',
            'C2': '#54a0ff'
        }
        color = colors.get(obj.proficiency_level, '#95afc0')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 5px; font-weight: bold; font-size: 14px;">{}</span>',
            color, obj.proficiency_level
        )
    display_proficiency.short_description = 'Level'

    def display_improvement(self, obj):
        """Display improvement from last assessment"""
        improvement = obj.improvement_from_last or 0

        if improvement > 0:
            arrow = '↑'
            color = '#28a745'
            sign = '+'
        elif improvement < 0:
            arrow = '↓'
            color = '#dc3545'
            sign = ''
        else:
            arrow = '→'
            color = '#6c757d'
            sign = ''

        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 16px;">'
            '{} {}{:.1f}%</span>',
            color, arrow, sign, improvement
        )
    display_improvement.short_description = 'Change'

    def display_skill_breakdown(self, obj):
        """Display skill scores breakdown"""
        skills = [
            ('🎯 Pronunciation', obj.pronunciation_score),
            ('💬 Fluency', obj.fluency_score),
            ('📚 Vocabulary', obj.vocabulary_score),
            ('✏️ Grammar', obj.grammar_score),
            ('🔗 Coherence', obj.coherence_score)
        ]

        html = '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">'
        html += '<strong>Skill Breakdown:</strong><br>'

        for skill, score in skills:
            color = '#28a745' if score >= 70 else '#ffc107' if score >= 50 else '#dc3545'
            html += format_html(
                '{}: <span style="color: {}; font-weight: bold;">{:.1f}%</span><br>',
                skill, color, score
            )

        html += '</div>'
        return format_html(html)
    display_skill_breakdown.short_description = 'Skills'

    def display_strengths_weaknesses(self, obj):
        """Display strengths and weaknesses"""
        html = '<div style="padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
        html += 'color: white; border-radius: 5px;">'

        if obj.strengths:
            html += '<strong>💪 Strengths:</strong><br>'
            for strength in obj.strengths[:3]:
                html += f'• {strength}<br>'

        if obj.weaknesses:
            html += '<br><strong>🎯 Areas to Improve:</strong><br>'
            for weakness in obj.weaknesses[:3]:
                html += f'• {weakness}<br>'

        html += '</div>'
        return format_html(html)
    display_strengths_weaknesses.short_description = 'Analysis'

    def display_recommendations(self, obj):
        """Display personalized recommendations"""
        if not obj.recommendations:
            return 'No recommendations available'

        html = '<div style="padding: 10px; background: #d4edda; border-radius: 5px;">'
        html += '<strong>📝 Recommendations:</strong><br>'

        for i, rec in enumerate(obj.recommendations[:5], 1):
            html += f'{i}. {rec}<br>'

        html += '</div>'
        return format_html(html)
    display_recommendations.short_description = 'Recommendations'


@admin.register(ChatModeUsage)
class ChatModeUsageAdmin(admin.ModelAdmin):
    """Admin for ChatModeUsage - Track Text vs Voice chat usage"""
    list_display = [
        'user',
        'display_mode',
        'display_status',
        'started_at',
        'display_duration',
        'message_count',
        'device_info'
    ]
    list_filter = [
        'mode',
        'is_active',
        'started_at',
        'device_info'
    ]
    search_fields = ['user__username', 'user__email', 'user__display_name', 'session_id']
    readonly_fields = [
        'usage_id',
        'session_id',
        'started_at',
        'created_at',
        'updated_at',
        'display_session_info'
    ]
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('User & Session', {
            'fields': (
                'user',
                'usage_id',
                'session_id',
                'display_session_info'
            )
        }),
        ('Chat Mode', {
            'fields': (
                'mode',
                'is_active',
                'message_count'
            )
        }),
        ('Timing', {
            'fields': (
                'started_at',
                'ended_at',
                'duration_seconds'
            )
        }),
        ('Device Info', {
            'fields': (
                'device_info',
                'app_version'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_ended', 'export_stats']
    
    def display_mode(self, obj):
        """Display mode with icon"""
        icons = {
            'text': '💬',
            'voice': '🎤'
        }
        colors = {
            'text': '#3498db',
            'voice': '#e74c3c'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            colors.get(obj.mode, '#000'),
            icons.get(obj.mode, ''),
            obj.get_mode_display()
        )
    display_mode.short_description = 'Mode'
    display_mode.admin_order_field = 'mode'
    
    def display_status(self, obj):
        """Display active status"""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">● ACTIVE</span>'
            )
        else:
            return format_html(
                '<span style="color: #6c757d;">● Ended</span>'
            )
    display_status.short_description = 'Status'
    display_status.admin_order_field = 'is_active'
    
    def display_duration(self, obj):
        """Display session duration"""
        duration = obj.calculate_duration()
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745;">{}m {}s (ongoing)</span>',
                minutes, seconds
            )
        else:
            return f'{minutes}m {seconds}s'
    display_duration.short_description = 'Duration'
    
    def display_session_info(self, obj):
        """Display comprehensive session information"""
        duration = obj.calculate_duration()
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        html = '<div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        
        rows = [
            ('👤 User', f'{obj.user.display_name or obj.user.username} ({obj.user.email})'),
            ('💬/🎤 Mode', f'<strong>{obj.get_mode_display()}</strong>'),
            ('🆔 Session ID', str(obj.session_id)),
            ('⏰ Started', obj.started_at.strftime('%Y-%m-%d %H:%M:%S')),
        ]
        
        if obj.ended_at:
            rows.append(('🏁 Ended', obj.ended_at.strftime('%Y-%m-%d %H:%M:%S')))
        
        rows.extend([
            ('⏱️ Duration', f'{minutes} min {seconds} sec'),
            ('💬 Messages', str(obj.message_count)),
            ('📱 Device', obj.device_info or 'Not specified'),
            ('📲 App Version', obj.app_version or 'Not specified'),
            ('✅ Status', '<span style="color: green;">Active</span>' if obj.is_active else '<span style="color: gray;">Ended</span>')
        ])
        
        for label, value in rows:
            html += f'<tr><td style="padding: 5px; font-weight: bold;">{label}:</td><td style="padding: 5px;">{value}</td></tr>'
        
        html += '</table></div>'
        return format_html(html)
    display_session_info.short_description = 'Session Details'
    
    def mark_as_ended(self, request, queryset):
        """Mark selected sessions as ended"""
        count = 0
        for usage in queryset.filter(is_active=True):
            usage.end_session()
            count += 1
        
        self.message_user(
            request,
            f'{count} session(s) marked as ended.',
            'success'
        )
    mark_as_ended.short_description = 'Mark selected as ended'
    
    def export_stats(self, request, queryset):
        """Export statistics for selected sessions"""
        from django.http import HttpResponse
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="chat_mode_stats.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'User Email', 'Username', 'Mode', 'Started At', 'Ended At',
            'Duration (seconds)', 'Messages', 'Device', 'App Version', 'Status'
        ])
        
        for usage in queryset:
            writer.writerow([
                usage.user.email,
                usage.user.username,
                usage.mode,
                usage.started_at,
                usage.ended_at if usage.ended_at else 'Active',
                usage.calculate_duration(),
                usage.message_count,
                usage.device_info,
                usage.app_version,
                'Active' if usage.is_active else 'Ended'
            ])
        
        return response
    export_stats.short_description = 'Export stats to CSV'
    
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to the change list view"""
        extra_context = extra_context or {}
        
        # Calculate aggregate stats
        total_sessions = ChatModeUsage.objects.count()
        active_sessions = ChatModeUsage.objects.filter(is_active=True).count()
        text_sessions = ChatModeUsage.objects.filter(mode='text').count()
        voice_sessions = ChatModeUsage.objects.filter(mode='voice').count()
        
        # Get unique users
        unique_users = ChatModeUsage.objects.values('user').distinct().count()
        
        # Get currently active users
        active_users = ChatModeUsage.objects.filter(
            is_active=True
        ).values('user').distinct().count()
        
        extra_context['summary_stats'] = {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'text_sessions': text_sessions,
            'voice_sessions': voice_sessions,
            'text_percentage': round((text_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1),
            'voice_percentage': round((voice_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1),
            'unique_users': unique_users,
            'active_users': active_users
        }
        
        return super().changelist_view(request, extra_context)
