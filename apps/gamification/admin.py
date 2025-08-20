"""
Admin configuration for Gamification app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserLevel,
    Badge,
    UserBadge,
    GotongRoyongChallenge,
    ChallengeParticipation,
    Leaderboard,
    LeaderboardEntry,
    DailyQuest,
    UserQuest,
    RewardShop,
    UserReward
)


@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    """
    Admin interface for User Levels
    """
    list_display = [
        'user', 'current_level', 'experience_points', 'wayang_character',
        'streak_days', 'mentor', 'last_activity_date'
    ]
    list_filter = [
        'current_level', 'wayang_character', 'last_activity_date'
    ]
    search_fields = ['user__email', 'user__username']
    ordering = ['-current_level', '-experience_points']

    readonly_fields = [
        'created_at', 'updated_at', 'total_points_earned'
    ]

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'mentor', 'mentor_since')
        }),
        ('Level & Experience', {
            'fields': (
                'current_level', 'experience_points', 'total_points_earned',
                'wayang_character'
            )
        }),
        ('Streak Information', {
            'fields': (
                'streak_days', 'longest_streak', 'last_activity_date'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    """
    Admin interface for Badges
    """
    list_display = [
        'name', 'category', 'batik_pattern', 'tier_display', 'points_value', 'is_active'
    ]
    list_filter = [
        'category', 'batik_pattern', 'tier', 'is_active'
    ]
    search_fields = ['name', 'description']
    ordering = ['category', 'tier', 'name']

    readonly_fields = ['badge_id', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('badge_id', 'name', 'description', 'category')
        }),
        ('Batik Pattern Theme', {
            'fields': ('batik_pattern', 'pattern_color')
        }),
        ('Requirements & Rewards', {
            'fields': ('requirements', 'points_value', 'tier')
        }),
        ('Visual Elements', {
            'fields': ('icon', 'image_url')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        })
    )

    def tier_display(self, obj):
        """Display tier with color"""
        colors = {1: 'brown', 2: 'silver', 3: 'gold', 4: 'purple', 5: 'blue'}
        tier_names = {1: 'Bronze', 2: 'Silver', 3: 'Gold', 4: 'Platinum', 5: 'Diamond'}
        color = colors.get(obj.tier, 'black')
        name = tier_names.get(obj.tier, 'Unknown')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, name
        )
    tier_display.short_description = 'Tier'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    """
    Admin interface for User Badges
    """
    list_display = [
        'user', 'badge', 'current_tier', 'earned_at'
    ]
    list_filter = ['earned_at', 'current_tier']
    search_fields = ['user__email', 'badge__name']
    ordering = ['-earned_at']

    readonly_fields = ['earned_at']

    fieldsets = (
        ('Badge Assignment', {
            'fields': ('user', 'badge', 'current_tier')
        }),
        ('Progress', {
            'fields': ('progress_data',)
        }),
        ('Timestamps', {
            'fields': ('earned_at',)
        })
    )


@admin.register(GotongRoyongChallenge)
class GotongRoyongChallengeAdmin(admin.ModelAdmin):
    """
    Admin interface for Gotong Royong Challenges
    """
    list_display = [
        'name', 'challenge_type', 'participant_count',
        'is_active', 'start_date', 'end_date'
    ]
    list_filter = [
        'challenge_type', 'is_active', 'start_date'
    ]
    search_fields = ['name', 'description']
    ordering = ['-start_date']

    readonly_fields = ['challenge_id', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('challenge_id', 'name', 'description', 'challenge_type')
        }),
        ('Participation', {
            'fields': (
                'minimum_participants', 'maximum_participants',
                'duration_days'
            )
        }),
        ('Goals & Rewards', {
            'fields': (
                'goal_description', 'goal_target',
                'reward_points', 'reward_badge'
            )
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def participant_count(self, obj):
        """Get current participant count"""
        return obj.participants.filter(is_active=True).count()
    participant_count.short_description = 'Participants'


@admin.register(ChallengeParticipation)
class ChallengeParticipationAdmin(admin.ModelAdmin):
    """
    Admin interface for Challenge Participation
    """
    list_display = [
        'user', 'challenge', 'contribution_score',
        'is_active', 'completed', 'joined_at'
    ]
    list_filter = ['is_active', 'completed', 'joined_at']
    search_fields = ['user__email', 'challenge__name']
    ordering = ['-joined_at']

    readonly_fields = ['joined_at', 'completed_at']

    fieldsets = (
        ('Participation', {
            'fields': ('user', 'challenge')
        }),
        ('Progress', {
            'fields': (
                'contribution_score', 'is_active',
                'completed', 'final_score'
            )
        }),
        ('Timestamps', {
            'fields': ('joined_at', 'completed_at')
        })
    )


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """
    Admin interface for Leaderboards
    """
    list_display = [
        'leaderboard_type', 'region', 'period_start',
        'period_end', 'last_updated'
    ]
    list_filter = ['leaderboard_type', 'region']
    ordering = ['-period_start']

    readonly_fields = ['last_updated']

    fieldsets = (
        ('Leaderboard Type', {
            'fields': ('leaderboard_type', 'region')
        }),
        ('Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Data', {
            'fields': ('rankings', 'last_updated')
        })
    )


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    """
    Admin interface for Leaderboard Entries
    """
    list_display = [
        'user', 'leaderboard', 'rank', 'score',
        'wayang_character', 'created_at'
    ]
    list_filter = ['leaderboard__leaderboard_type', 'created_at']
    search_fields = ['user__email', 'user__username']
    ordering = ['leaderboard', 'rank']

    readonly_fields = ['created_at']

    fieldsets = (
        ('Entry Information', {
            'fields': ('leaderboard', 'user', 'rank', 'score')
        }),
        ('Statistics', {
            'fields': (
                'sessions_completed', 'average_score',
                'improvement_rate'
            )
        }),
        ('Cultural Elements', {
            'fields': ('wayang_character', 'primary_badge')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )


@admin.register(DailyQuest)
class DailyQuestAdmin(admin.ModelAdmin):
    """
    Admin interface for Daily Quests
    """
    list_display = [
        'name', 'quest_type', 'target_value',
        'experience_points', 'is_active', 'available_date'
    ]
    list_filter = ['quest_type', 'is_active', 'available_date']
    search_fields = ['name', 'description']
    ordering = ['-available_date']

    readonly_fields = ['quest_id', 'created_at']

    fieldsets = (
        ('Quest Information', {
            'fields': ('quest_id', 'name', 'description', 'quest_type')
        }),
        ('Requirements', {
            'fields': ('requirements', 'target_value')
        }),
        ('Rewards', {
            'fields': ('experience_points', 'bonus_points')
        }),
        ('Availability', {
            'fields': ('is_active', 'available_date')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(UserQuest)
class UserQuestAdmin(admin.ModelAdmin):
    """
    Admin interface for User Quest Progress
    """
    list_display = [
        'user', 'quest', 'progress_display',
        'is_completed', 'points_earned', 'started_at'
    ]
    list_filter = ['is_completed', 'rewards_claimed', 'started_at']
    search_fields = ['user__email', 'quest__name']
    ordering = ['-started_at']

    readonly_fields = ['started_at', 'completed_at']

    fieldsets = (
        ('Quest Assignment', {
            'fields': ('user', 'quest')
        }),
        ('Progress', {
            'fields': (
                'current_progress', 'is_completed',
                'points_earned', 'rewards_claimed'
            )
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at')
        })
    )

    def progress_display(self, obj):
        """Display progress as percentage"""
        if obj.quest.target_value > 0:
            percentage = (obj.current_progress / obj.quest.target_value) * 100
            color = 'green' if percentage >= 100 else 'orange' if percentage >= 50 else 'red'
            return format_html(
                '<span style="color: {};">{:.0f}%</span>',
                color, min(100, percentage)
            )
        return '-'
    progress_display.short_description = 'Progress'


@admin.register(RewardShop)
class RewardShopAdmin(admin.ModelAdmin):
    """
    Admin interface for Reward Shop
    """
    list_display = [
        'name', 'reward_type', 'point_cost', 'level_requirement',
        'stock_display', 'is_active'
    ]
    list_filter = [
        'reward_type', 'is_active', 'is_limited'
    ]
    search_fields = ['name', 'description', 'cultural_reference']
    ordering = ['point_cost', 'name']

    readonly_fields = ['reward_id', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('reward_id', 'name', 'description', 'reward_type')
        }),
        ('Cost & Requirements', {
            'fields': ('point_cost', 'level_requirement')
        }),
        ('Visual Elements', {
            'fields': ('icon', 'preview_image')
        }),
        ('Cultural Theme', {
            'fields': ('cultural_reference',)
        }),
        ('Stock & Availability', {
            'fields': ('is_limited', 'stock_remaining', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def stock_display(self, obj):
        """Display stock status"""
        if not obj.is_limited:
            return format_html('<span style="color: green;">Unlimited</span>')
        elif obj.stock_remaining is None:
            return '-'
        elif obj.stock_remaining == 0:
            return format_html('<span style="color: red;">Out of Stock</span>')
        elif obj.stock_remaining < 10:
            return format_html(
                '<span style="color: orange;">Low ({} left)</span>',
                obj.stock_remaining
            )
        else:
            return format_html(
                '<span style="color: green;">{} available</span>',
                obj.stock_remaining
            )
    stock_display.short_description = 'Stock'


@admin.register(UserReward)
class UserRewardAdmin(admin.ModelAdmin):
    """
    Admin interface for User Rewards
    """
    list_display = [
        'user', 'reward', 'acquisition_type',
        'is_active', 'equipped_at', 'acquired_at'
    ]
    list_filter = [
        'acquisition_type', 'is_active', 'acquired_at'
    ]
    search_fields = ['user__email', 'reward__name']
    ordering = ['-acquired_at']

    readonly_fields = ['acquired_at']

    fieldsets = (
        ('Reward Assignment', {
            'fields': ('user', 'reward')
        }),
        ('Acquisition', {
            'fields': ('acquisition_type', 'acquired_at')
        }),
        ('Usage', {
            'fields': ('is_active', 'equipped_at')
        })
    )
