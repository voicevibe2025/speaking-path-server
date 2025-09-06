"""
Models for Gamification with Indonesian Cultural Elements
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class UserLevel(models.Model):
    """
    User level and experience tracking
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='level_profile')

    # Level and experience
    current_level = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    experience_points = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    total_points_earned = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    # Wayang character progression (Indonesian shadow puppet characters)
    wayang_character = models.CharField(
        max_length=50,
        default='Semar',
        choices=(
            ('Semar', 'Semar - The Wise Beginner'),
            ('Gareng', 'Gareng - The Determined Learner'),
            ('Petruk', 'Petruk - The Eloquent Speaker'),
            ('Bagong', 'Bagong - The Confident Communicator'),
            ('Arjuna', 'Arjuna - The Skilled Practitioner'),
            ('Bima', 'Bima - The Strong Achiever'),
            ('Yudhistira', 'Yudhistira - The Master Speaker')
        )
    )

    # Mentor-student hierarchy (Indonesian cultural aspect)
    mentor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mentees'
    )
    mentor_since = models.DateTimeField(null=True, blank=True)

    # Statistics
    streak_days = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-current_level', '-experience_points']

    def __str__(self):
        return f"{self.user.username} - Level {self.current_level} ({self.wayang_character})"


class Badge(models.Model):
    """
    Badges with Batik pattern themes
    """
    BADGE_CATEGORIES = (
        ('pronunciation', 'Pronunciation'),
        ('grammar', 'Grammar'),
        ('fluency', 'Fluency'),
        ('vocabulary', 'Vocabulary'),
        ('cultural', 'Cultural Understanding'),
        ('streak', 'Consistency'),
        ('collaboration', 'Gotong Royong'),
        ('special', 'Special Achievement')
    )

    BATIK_PATTERNS = (
        ('kawung', 'Kawung - Wisdom and Justice'),
        ('parang', 'Parang - Strength and Continuity'),
        ('sido_mukti', 'Sido Mukti - Prosperity'),
        ('truntum', 'Truntum - Love and Loyalty'),
        ('mega_mendung', 'Mega Mendung - Patience'),
        ('sekar_jagad', 'Sekar Jagad - Diversity'),
        ('ceplok', 'Ceplok - Harmony and Balance')
    )

    badge_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=BADGE_CATEGORIES)

    # Batik pattern theme
    batik_pattern = models.CharField(max_length=20, choices=BATIK_PATTERNS)
    pattern_color = models.CharField(max_length=7, default='#000000', help_text='Hex color code')

    # Requirements
    requirements = models.JSONField(default=dict)
    points_value = models.IntegerField(default=50)

    # Visual elements
    icon = models.CharField(max_length=50)
    image_url = models.URLField(null=True, blank=True)

    # Rarity and progression
    tier = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='1=Bronze, 2=Silver, 3=Gold, 4=Platinum, 5=Diamond'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'tier', 'name']

    def __str__(self):
        return f"{self.name} ({self.batik_pattern})"


class UserBadge(models.Model):
    """
    Track user's earned badges
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')

    earned_at = models.DateTimeField(auto_now_add=True)
    progress_data = models.JSONField(default=dict, help_text='Progress towards next tier')
    current_tier = models.IntegerField(default=1)

    class Meta:
        ordering = ['-earned_at']
        unique_together = [['user', 'badge']]

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class GotongRoyongChallenge(models.Model):
    """
    Collaborative challenges based on Indonesian Gotong Royong concept
    (mutual cooperation and community help)
    """
    challenge_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()

    # Challenge type
    challenge_type = models.CharField(
        max_length=30,
        choices=(
            ('group_practice', 'Group Practice Session'),
            ('peer_review', 'Peer Review Exchange'),
            ('pronunciation_relay', 'Pronunciation Relay'),
            ('vocabulary_building', 'Collaborative Vocabulary Building'),
            ('cultural_exchange', 'Cultural Exchange'),
            ('storytelling', 'Chain Storytelling')
        )
    )

    # Requirements
    minimum_participants = models.IntegerField(default=2)
    maximum_participants = models.IntegerField(default=10)
    duration_days = models.IntegerField(default=7)

    # Goals and rewards
    goal_description = models.TextField()
    goal_target = models.IntegerField(help_text='Target score/count/etc.')
    reward_points = models.IntegerField(default=100)
    reward_badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class ChallengeParticipation(models.Model):
    """
    Track user participation in Gotong Royong challenges
    """
    challenge = models.ForeignKey(
        GotongRoyongChallenge,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_participations')

    # Participation details
    joined_at = models.DateTimeField(auto_now_add=True)
    contribution_score = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Results
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    final_score = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-joined_at']
        unique_together = [['challenge', 'user']]

    def __str__(self):
        return f"{self.user.username} - {self.challenge.name}"


class Leaderboard(models.Model):
    """
    Different types of leaderboards
    """
    LEADERBOARD_TYPES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('all_time', 'All Time'),
        ('pronunciation', 'Pronunciation Masters'),
        ('fluency', 'Fluency Champions'),
        ('gotong_royong', 'Gotong Royong Leaders'),
        ('regional', 'Regional (Indonesian Provinces)')
    )

    leaderboard_type = models.CharField(max_length=20, choices=LEADERBOARD_TYPES)
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)

    # Regional specification for Indonesian provinces
    region = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='Indonesian province for regional leaderboards'
    )

    # Cached rankings (updated periodically)
    rankings = models.JSONField(default=list)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period_start']
        unique_together = [['leaderboard_type', 'period_start', 'region']]

    def __str__(self):
        return f"{self.get_leaderboard_type_display()} Leaderboard"


class LeaderboardEntry(models.Model):
    """
    Individual entries in leaderboards
    """
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name='entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')

    rank = models.IntegerField()
    score = models.IntegerField()

    # Additional stats
    sessions_completed = models.IntegerField(default=0)
    average_score = models.FloatField(default=0)
    improvement_rate = models.FloatField(default=0)

    # Cultural elements displayed
    wayang_character = models.CharField(max_length=50, null=True, blank=True)
    primary_badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['leaderboard', 'rank']
        unique_together = [['leaderboard', 'user']]

    def __str__(self):
        return f"{self.user.username} - Rank {self.rank}"


class PointsTransaction(models.Model):
    """
    Timestamped log of points (XP) earned or spent.

    We record positive amounts for earnings (practice rewards, quests, streak bonuses, challenges, etc.).
    Negative amounts may be used for spends (e.g., shop purchases), but leaderboards will only aggregate
    positive earnings per time window.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points_transactions')
    amount = models.IntegerField(help_text='Positive for earnings; negative for spends/deductions')
    source = models.CharField(max_length=50, help_text='origin label e.g. pronunciation, daily_quest, streak_bonus, challenge, manual')
    context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f"{self.user.username} {sign}{self.amount} ({self.source}) @ {self.created_at}"


class DailyQuest(models.Model):
    """
    Daily quests for consistent practice
    """
    QUEST_TYPES = (
        ('speaking_practice', 'Complete Speaking Practice'),
        ('pronunciation', 'Pronunciation Exercise'),
        ('vocabulary', 'Learn New Vocabulary'),
        ('grammar', 'Grammar Challenge'),
        ('cultural', 'Cultural Scenario'),
        ('peer_review', 'Review Peer Recording'),
        ('streak', 'Maintain Streak')
    )

    quest_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    quest_type = models.CharField(max_length=20, choices=QUEST_TYPES)

    # Requirements
    requirements = models.JSONField(default=dict)
    target_value = models.IntegerField(default=1)

    # Rewards
    experience_points = models.IntegerField(default=10)
    bonus_points = models.IntegerField(default=5, help_text='Bonus for completion streak')

    # Availability
    is_active = models.BooleanField(default=True)
    available_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-available_date']

    def __str__(self):
        return f"{self.name} ({self.available_date})"


class UserQuest(models.Model):
    """
    Track user's daily quest progress
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_quests')
    quest = models.ForeignKey(DailyQuest, on_delete=models.CASCADE, related_name='user_progress')

    # Progress
    current_progress = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Rewards claimed
    points_earned = models.IntegerField(default=0)
    rewards_claimed = models.BooleanField(default=False)

    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']
        unique_together = [['user', 'quest']]

    def __str__(self):
        return f"{self.user.username} - {self.quest.name}"


class RewardShop(models.Model):
    """
    Virtual reward shop for spending earned points
    """
    REWARD_TYPES = (
        ('avatar_frame', 'Wayang Avatar Frame'),
        ('title', 'Special Title'),
        ('voice_pack', 'Voice Feedback Pack'),
        ('theme', 'App Theme'),
        ('boost', 'XP Boost'),
        ('unlock', 'Content Unlock'),
        ('cultural', 'Cultural Content')
    )

    reward_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)

    # Cost and availability
    point_cost = models.IntegerField(validators=[MinValueValidator(0)])
    level_requirement = models.IntegerField(default=1)

    # Visual elements
    icon = models.CharField(max_length=50)
    preview_image = models.URLField(null=True, blank=True)

    # Cultural theme
    cultural_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='Indonesian cultural reference'
    )

    # Stock and availability
    is_limited = models.BooleanField(default=False)
    stock_remaining = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['point_cost', 'name']

    def __str__(self):
        return f"{self.name} ({self.point_cost} points)"


class UserReward(models.Model):
    """
    Track user's purchased/earned rewards
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rewards')
    reward = models.ForeignKey(RewardShop, on_delete=models.CASCADE, related_name='user_purchases')

    # Acquisition details
    acquired_at = models.DateTimeField(auto_now_add=True)
    acquisition_type = models.CharField(
        max_length=20,
        choices=(
            ('purchase', 'Purchased'),
            ('achievement', 'Achievement Reward'),
            ('event', 'Event Reward'),
            ('gift', 'Gifted')
        ),
        default='purchase'
    )

    # Usage
    is_active = models.BooleanField(default=True)
    equipped_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-acquired_at']

    def __str__(self):
        return f"{self.user.username} - {self.reward.name}"
