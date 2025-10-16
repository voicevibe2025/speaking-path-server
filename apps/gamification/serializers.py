"""
Serializers for Gamification app
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
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
    UserReward,
    AchievementEvent,
)

User = get_user_model()


class UserLevelSerializer(serializers.ModelSerializer):
    """
    Serializer for user level and experience
    """
    user = serializers.StringRelatedField(read_only=True)
    mentor_username = serializers.CharField(source='mentor.username', read_only=True)
    next_level_points = serializers.SerializerMethodField()
    
    class Meta:
        model = UserLevel
        fields = [
            'user', 'current_level', 'experience_points', 'total_points_earned',
            'wayang_character', 'mentor', 'mentor_username', 'mentor_since',
            'streak_days', 'longest_streak', 'last_activity_date',
            'next_level_points', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_next_level_points(self, obj):
        """Calculate points needed for next level"""
        # Option A progression: xp required to go from L -> L+1 is 100 + 25*(L-1)
        try:
            level = int(getattr(obj, 'current_level', 1) or 1)
        except Exception:
            level = 1
        return max(1, 100 + 25 * (level - 1))


class BadgeSerializer(serializers.ModelSerializer):
    """
    Serializer for badges with Batik patterns
    """
    tier_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Badge
        fields = [
            'badge_id', 'name', 'description', 'category', 'batik_pattern',
            'pattern_color', 'requirements', 'points_value', 'icon',
            'image_url', 'tier', 'tier_display', 'is_active', 'created_at'
        ]
    
    def get_tier_display(self, obj):
        """Return tier name"""
        tier_names = {
            1: 'Bronze',
            2: 'Silver',
            3: 'Gold',
            4: 'Platinum',
            5: 'Diamond'
        }
        return tier_names.get(obj.tier, 'Unknown')


class UserBadgeSerializer(serializers.ModelSerializer):
    """
    Serializer for user's earned badges
    """
    badge = BadgeSerializer(read_only=True)
    badge_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = UserBadge
        fields = [
            'id', 'user', 'badge', 'badge_id', 'earned_at',
            'progress_data', 'current_tier'
        ]
        read_only_fields = ['user', 'earned_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        badge_id = validated_data.pop('badge_id')
        validated_data['badge'] = Badge.objects.get(badge_id=badge_id)
        return super().create(validated_data)


class GotongRoyongChallengeSerializer(serializers.ModelSerializer):
    """
    Serializer for collaborative challenges
    """
    participant_count = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    reward_badge_info = BadgeSerializer(source='reward_badge', read_only=True)
    
    class Meta:
        model = GotongRoyongChallenge
        fields = [
            'challenge_id', 'name', 'description', 'challenge_type',
            'minimum_participants', 'maximum_participants', 'duration_days',
            'goal_description', 'goal_target', 'reward_points', 'reward_badge',
            'reward_badge_info', 'is_active', 'start_date', 'end_date',
            'participant_count', 'days_remaining', 'created_at'
        ]
    
    def get_participant_count(self, obj):
        """Get current number of participants"""
        return obj.participants.filter(is_active=True).count()
    
    def get_days_remaining(self, obj):
        """Calculate days remaining in challenge"""
        from django.utils import timezone
        if obj.end_date:
            delta = obj.end_date - timezone.now()
            return max(0, delta.days)
        return 0


class ChallengeParticipationSerializer(serializers.ModelSerializer):
    """
    Serializer for challenge participation
    """
    challenge_name = serializers.CharField(source='challenge.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ChallengeParticipation
        fields = [
            'id', 'challenge', 'challenge_name', 'user', 'username',
            'joined_at', 'contribution_score', 'is_active',
            'completed', 'completed_at', 'final_score'
        ]
        read_only_fields = ['joined_at', 'completed_at']


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for leaderboard entries
    """
    username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    badge_info = BadgeSerializer(source='primary_badge', read_only=True)
    user_level = serializers.SerializerMethodField()
    streak_days = serializers.SerializerMethodField()
    
    class Meta:
        model = LeaderboardEntry
        fields = [
            'rank', 'user', 'username', 'user_avatar', 'score',
            'sessions_completed', 'average_score', 'improvement_rate',
            'wayang_character', 'primary_badge', 'badge_info', 'created_at',
            'user_level', 'streak_days'
        ]
    
    def get_user_avatar(self, obj):
        """Return the user's avatar URL, preferring uploaded image over legacy URL."""
        request = self.context.get('request') if hasattr(self, 'context') else None
        try:
            profile = obj.user.profile  # OneToOne related_name='profile'
            if profile and getattr(profile, 'avatar', None) and hasattr(profile.avatar, 'url'):
                return request.build_absolute_uri(profile.avatar.url) if request else profile.avatar.url
            if profile and getattr(profile, 'avatar_url', None):
                return profile.avatar_url
        except Exception:
            pass
        return None

    def get_user_level(self, obj):
        """Get the user's current level for this leaderboard entry"""
        try:
            return obj.user.level_profile.current_level
        except Exception:
            return 0

    def get_streak_days(self, obj):
        """Get the user's current streak days for this leaderboard entry"""
        try:
            return obj.user.level_profile.streak_days
        except Exception:
            return 0


class LeaderboardSerializer(serializers.ModelSerializer):
    """
    Serializer for leaderboards
    """
    entries = LeaderboardEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = Leaderboard
        fields = [
            'id', 'leaderboard_type', 'period_start', 'period_end',
            'region', 'rankings', 'last_updated', 'entries'
        ]


class DailyQuestSerializer(serializers.ModelSerializer):
    """
    Serializer for daily quests
    """
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyQuest
        fields = [
            'quest_id', 'name', 'description', 'quest_type',
            'requirements', 'target_value', 'experience_points',
            'bonus_points', 'is_active', 'available_date',
            'user_progress', 'created_at'
        ]
    
    def get_user_progress(self, obj):
        """Get current user's progress on this quest"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = UserQuest.objects.get(user=request.user, quest=obj)
                return {
                    'current_progress': progress.current_progress,
                    'is_completed': progress.is_completed,
                    'points_earned': progress.points_earned
                }
            except UserQuest.DoesNotExist:
                return None
        return None


class UserQuestSerializer(serializers.ModelSerializer):
    """
    Serializer for user quest progress
    """
    quest_details = DailyQuestSerializer(source='quest', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UserQuest
        fields = [
            'id', 'user', 'quest', 'quest_details', 'current_progress',
            'is_completed', 'completed_at', 'points_earned',
            'rewards_claimed', 'started_at', 'progress_percentage'
        ]
        read_only_fields = ['user', 'started_at', 'completed_at']
    
    def get_progress_percentage(self, obj):
        """Calculate progress percentage"""
        if obj.quest.target_value > 0:
            return min(100, (obj.current_progress / obj.quest.target_value) * 100)
        return 0


class RewardShopSerializer(serializers.ModelSerializer):
    """
    Serializer for reward shop items
    """
    can_afford = serializers.SerializerMethodField()
    meets_level_requirement = serializers.SerializerMethodField()
    
    class Meta:
        model = RewardShop
        fields = [
            'reward_id', 'name', 'description', 'reward_type',
            'point_cost', 'level_requirement', 'icon', 'preview_image',
            'cultural_reference', 'is_limited', 'stock_remaining',
            'is_active', 'can_afford', 'meets_level_requirement', 'created_at'
        ]
    
    def get_can_afford(self, obj):
        """Check if user can afford this reward"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                user_level = UserLevel.objects.get(user=request.user)
                return user_level.total_points_earned >= obj.point_cost
            except UserLevel.DoesNotExist:
                return False
        return False
    
    def get_meets_level_requirement(self, obj):
        """Check if user meets level requirement"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                user_level = UserLevel.objects.get(user=request.user)
                return user_level.current_level >= obj.level_requirement
            except UserLevel.DoesNotExist:
                return False
        return False


class UserRewardSerializer(serializers.ModelSerializer):
    """
    Serializer for user rewards
    """
    reward_details = RewardShopSerializer(source='reward', read_only=True)
    
    class Meta:
        model = UserReward
        fields = [
            'id', 'user', 'reward', 'reward_details', 'acquired_at',
            'acquisition_type', 'is_active', 'equipped_at'
        ]
        read_only_fields = ['user', 'acquired_at']


class AchievementEventSerializer(serializers.ModelSerializer):
    """
    Serializer for persistent achievement events
    """
    class Meta:
        model = AchievementEvent
        fields = [
            'id', 'event_type', 'title', 'description', 'timestamp',
            'xp_earned', 'meta'
        ]
        read_only_fields = fields


class PurchaseRewardSerializer(serializers.Serializer):
    """
    Serializer for purchasing rewards
    """
    reward_id = serializers.UUIDField()
    
    def validate_reward_id(self, value):
        """Validate reward exists and is available"""
        try:
            reward = RewardShop.objects.get(reward_id=value, is_active=True)
            
            # Check stock if limited
            if reward.is_limited and reward.stock_remaining <= 0:
                raise serializers.ValidationError("Reward is out of stock")
            
            return value
        except RewardShop.DoesNotExist:
            raise serializers.ValidationError("Invalid reward ID")


class JoinChallengeSerializer(serializers.Serializer):
    """
    Serializer for joining a challenge
    """
    challenge_id = serializers.IntegerField()
    
    def validate_challenge_id(self, value):
        """Validate challenge exists and is joinable"""
        try:
            challenge = GotongRoyongChallenge.objects.get(
                id=value,
                is_active=True
            )
            
            # Check if challenge is full
            current_participants = challenge.participants.filter(is_active=True).count()
            if current_participants >= challenge.maximum_participants:
                raise serializers.ValidationError("Challenge is full")
            
            # Check if challenge has started
            from django.utils import timezone
            if challenge.start_date > timezone.now():
                raise serializers.ValidationError("Challenge has not started yet")
            
            if challenge.end_date < timezone.now():
                raise serializers.ValidationError("Challenge has ended")
            
            return value
        except GotongRoyongChallenge.DoesNotExist:
            raise serializers.ValidationError("Invalid challenge ID")


class UpdateStreakSerializer(serializers.Serializer):
    """
    Serializer for updating user practice streak
    """
    activity_type = serializers.CharField(
        max_length=50,
        required=False,
        default='practice'
    )
    session_id = serializers.IntegerField(required=False)
    
    def validate(self, attrs):
        """Validate streak update request"""
        activity_type = attrs.get('activity_type', 'practice')
        if activity_type not in ['practice', 'challenge', 'quest', 'session']:
            raise serializers.ValidationError(
                "Invalid activity type. Must be one of: practice, challenge, quest, session"
            )
        return attrs
