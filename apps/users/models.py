"""
User profile and related models for VoiceVibe
"""
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from core.storage import AvatarSupabaseStorage

User = get_user_model()


class Group(models.Model):
    """
    Batam cultural groups for collectivism feature.
    Each user belongs to one group.
    """
    GROUP_CHOICES = [
        ('gonggong', 'Gonggong'),
        ('pantun', 'Pantun'),
        ('zapin', 'Zapin'),
        ('hang_nadim', 'Hang Nadim'),
        ('barelang', 'Barelang'),
        ('bulan_serindit', 'Bulan Serindit'),
        ('selayar', 'Selayar'),
        ('tanjung_ulma', 'Tanjung Ulma'),
        ('pulau_putri', 'Pulau Putri'),
        ('temiang', 'Temiang'),
    ]
    
    name = models.CharField(
        max_length=50,
        unique=True,
        choices=GROUP_CHOICES,
        help_text=_('Batam cultural group name')
    )
    display_name = models.CharField(
        max_length=100,
        help_text=_('Display name for the group')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Description of the group and its cultural significance')
    )
    icon = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Icon or emoji representing the group')
    )
    color = models.CharField(
        max_length=7,
        default='#1976D2',
        help_text=_('Hex color code for the group theme')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'groups'
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')
        ordering = ['name']
    
    def __str__(self):
        return self.display_name
    
    @property
    def member_count(self):
        """Return the number of members in this group"""
        return self.members.count()


class GroupMessage(models.Model):
    """
    Messages sent in group chats
    """
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_messages'
    )
    message = models.TextField(
        help_text=_('Message content')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'group_messages'
        verbose_name = _('Group Message')
        verbose_name_plural = _('Group Messages')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['group', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} in {self.group.display_name}: {self.message[:50]}"


def user_avatar_path(instance, filename):
    """
    Generate upload path for user avatars
    """
    # Get file extension
    ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
    # Create filename with user ID
    return f"avatars/user_{instance.user.id}.{ext}"


class UserProfile(models.Model):
    """
    Extended user profile with learning preferences and cultural settings
    """
    PROFICIENCY_LEVELS = [
        ('beginner', _('Beginner')),
        ('elementary', _('Elementary')),
        ('intermediate', _('Intermediate')),
        ('upper_intermediate', _('Upper Intermediate')),
        ('advanced', _('Advanced')),
        ('proficient', _('Proficient')),
    ]

    LEARNING_GOALS = [
        ('business', _('Business Communication')),
        ('academic', _('Academic English')),
        ('conversational', _('Conversational English')),
        ('travel', _('Travel English')),
        ('professional', _('Professional Development')),
        ('exam_prep', _('Exam Preparation')),
    ]

    GENDER_CHOICES = [
        ('male', _('Male')),
        ('female', _('Female')),
    ]

    # Indonesian provinces (major ones)
    PROVINCE_CHOICES = [
        ('aceh', _('Aceh')),
        ('bali', _('Bali')),
        ('bangka_belitung', _('Bangka Belitung')),
        ('banten', _('Banten')),
        ('bengkulu', _('Bengkulu')),
        ('dki_jakarta', _('DKI Jakarta')),
        ('gorontalo', _('Gorontalo')),
        ('jambi', _('Jambi')),
        ('jawa_barat', _('Jawa Barat')),
        ('jawa_tengah', _('Jawa Tengah')),
        ('jawa_timur', _('Jawa Timur')),
        ('kalimantan_barat', _('Kalimantan Barat')),
        ('kalimantan_selatan', _('Kalimantan Selatan')),
        ('kalimantan_tengah', _('Kalimantan Tengah')),
        ('kalimantan_timur', _('Kalimantan Timur')),
        ('kalimantan_utara', _('Kalimantan Utara')),
        ('kepulauan_riau', _('Kepulauan Riau')),
        ('lampung', _('Lampung')),
        ('maluku', _('Maluku')),
        ('maluku_utara', _('Maluku Utara')),
        ('nusa_tenggara_barat', _('Nusa Tenggara Barat')),
        ('nusa_tenggara_timur', _('Nusa Tenggara Timur')),
        ('papua', _('Papua')),
        ('papua_barat', _('Papua Barat')),
        ('riau', _('Riau')),
        ('sulawesi_barat', _('Sulawesi Barat')),
        ('sulawesi_selatan', _('Sulawesi Selatan')),
        ('sulawesi_tengah', _('Sulawesi Tengah')),
        ('sulawesi_tenggara', _('Sulawesi Tenggara')),
        ('sulawesi_utara', _('Sulawesi Utara')),
        ('sumatera_barat', _('Sumatera Barat')),
        ('sumatera_selatan', _('Sumatera Selatan')),
        ('sumatera_utara', _('Sumatera Utara')),
        ('yogyakarta', _('DI Yogyakarta')),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # Personal Information
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        help_text=_('User gender for culturally-aware AI interactions')
    )
    province = models.CharField(
        max_length=50,
        choices=PROVINCE_CHOICES,
        null=True,
        blank=True,
        help_text=_('Indonesian province for regional socio-cultural context')
    )
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(
        upload_to=user_avatar_path, 
        storage=AvatarSupabaseStorage(), 
        null=True, 
        blank=True,
        help_text=_('User avatar image stored in Supabase Storage')
    )
    avatar_url = models.URLField(blank=True, help_text=_('Fallback avatar URL for external images'))
    bio = models.TextField(max_length=500, blank=True)

    # Language Settings
    native_language = models.CharField(
        max_length=10,
        default='id',  # Indonesian
        help_text=_('ISO 639-1 language code')
    )
    target_language = models.CharField(
        max_length=10,
        default='en',  # English
        help_text=_('ISO 639-1 language code')
    )
    current_proficiency = models.CharField(
        max_length=20,
        choices=PROFICIENCY_LEVELS,
        default='beginner'
    )

    # Learning Preferences
    learning_goal = models.CharField(
        max_length=20,
        choices=LEARNING_GOALS,
        default='conversational'
    )
    daily_practice_goal = models.IntegerField(
        default=15,  # minutes
        validators=[MinValueValidator(5), MaxValueValidator(120)],
        help_text=_('Daily practice goal in minutes')
    )
    preferred_session_duration = models.IntegerField(
        default=10,  # minutes
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        help_text=_('Preferred session duration in minutes')
    )

    # Cultural Preferences (Hofstede dimensions for Indonesia)
    power_distance_preference = models.FloatField(
        default=78.0,  # Indonesia's PDI score
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    individualism_preference = models.FloatField(
        default=14.0,  # Indonesia's IDV score
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    masculinity_preference = models.FloatField(
        default=46.0,  # Indonesia's MAS score
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    uncertainty_avoidance_preference = models.FloatField(
        default=48.0,  # Indonesia's UAI score
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    long_term_orientation_preference = models.FloatField(
        default=62.0,  # Indonesia's LTO score
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Gamification Settings
    preferred_reward_type = models.CharField(
        max_length=20,
        choices=[
            ('badges', _('Badges')),
            ('points', _('Points')),
            ('achievements', _('Achievements')),
            ('leaderboard', _('Leaderboard')),
        ],
        default='badges'
    )
    enable_notifications = models.BooleanField(default=True)
    enable_reminders = models.BooleanField(default=True)

    # Statistics
    total_practice_time = models.IntegerField(default=0)  # in minutes
    streak_days = models.IntegerField(default=0)
    last_practice_date = models.DateField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return f"Profile of {self.user.email}"


class LearningPreference(models.Model):
    """
    Detailed learning preferences and adaptations
    """
    SCENARIO_TYPES = [
        ('formal', _('Formal')),
        ('informal', _('Informal')),
        ('business', _('Business')),
        ('academic', _('Academic')),
        ('social', _('Social')),
        ('cultural', _('Cultural')),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='learning_preference'
    )

    # Scenario Preferences
    preferred_scenarios = models.JSONField(
        default=list,
        help_text=_('List of preferred scenario types')
    )
    avoided_topics = models.JSONField(
        default=list,
        help_text=_('List of topics to avoid')
    )

    # Learning Style
    visual_learning = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text=_('Preference for visual learning (1-10)')
    )
    auditory_learning = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text=_('Preference for auditory learning (1-10)')
    )
    kinesthetic_learning = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text=_('Preference for kinesthetic learning (1-10)')
    )

    # Feedback Preferences
    immediate_correction = models.BooleanField(
        default=True,
        help_text=_('Prefer immediate correction during practice')
    )
    detailed_feedback = models.BooleanField(
        default=True,
        help_text=_('Prefer detailed feedback after sessions')
    )
    cultural_context = models.BooleanField(
        default=True,
        help_text=_('Include cultural context in feedback')
    )

    # AI Adaptation Settings
    ai_personality = models.CharField(
        max_length=20,
        choices=[
            ('friendly', _('Friendly')),
            ('professional', _('Professional')),
            ('encouraging', _('Encouraging')),
            ('strict', _('Strict')),
            ('casual', _('Casual')),
        ],
        default='encouraging'
    )
    difficulty_adaptation_speed = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.1), MaxValueValidator(1.0)],
        help_text=_('How quickly to adapt difficulty (0.1-1.0)')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'learning_preferences'
        verbose_name = _('Learning Preference')
        verbose_name_plural = _('Learning Preferences')

    def __str__(self):
        return f"Learning preferences for {self.user.email}"


class UserAchievement(models.Model):
    """
    User achievements and milestones
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='achievements'
    )

    achievement_type = models.CharField(max_length=50)
    achievement_name = models.CharField(max_length=100)
    achievement_description = models.TextField()

    # Achievement metadata
    category = models.CharField(
        max_length=20,
        choices=[
            ('practice', _('Practice')),
            ('streak', _('Streak')),
            ('proficiency', _('Proficiency')),
            ('social', _('Social')),
            ('cultural', _('Cultural')),
        ]
    )
    points_earned = models.IntegerField(default=0)
    badge_image_url = models.URLField(blank=True)

    # Progress tracking
    progress_current = models.IntegerField(default=0)
    progress_target = models.IntegerField(default=1)
    is_completed = models.BooleanField(default=False)

    # Timestamps
    earned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_achievements'
        verbose_name = _('User Achievement')
        verbose_name_plural = _('User Achievements')
        unique_together = ['user', 'achievement_type']

    def __str__(self):
        return f"{self.achievement_name} - {self.user.email}"


class UserFollow(models.Model):
    """
    Simple follow relationship between users
    - follower follows following
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_relations'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower_relations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower']),
            models.Index(fields=['following']),
        ]

    def __str__(self):
        return f"{self.follower_id} -> {self.following_id}"


class UserBlock(models.Model):
    """
    User blocking relationship
    - blocker blocks blocked_user
    """
    blocker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocking_relations'
    )
    blocked_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocked_by_relations'
    )
    reason = models.TextField(blank=True, help_text=_('Optional reason for blocking'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_blocks'
        unique_together = ['blocker', 'blocked_user']
        indexes = [
            models.Index(fields=['blocker']),
            models.Index(fields=['blocked_user']),
        ]

    def __str__(self):
        return f"{self.blocker_id} blocked {self.blocked_user_id}"


class Report(models.Model):
    """
    User reports for content or users that violate community guidelines
    """
    REPORT_TYPE_USER = 'user'
    REPORT_TYPE_POST = 'post'
    REPORT_TYPE_COMMENT = 'comment'

    REPORT_TYPES = [
        (REPORT_TYPE_USER, 'User'),
        (REPORT_TYPE_POST, 'Post'),
        (REPORT_TYPE_COMMENT, 'Comment'),
    ]

    REASON_SPAM = 'spam'
    REASON_HARASSMENT = 'harassment'
    REASON_HATE_SPEECH = 'hate_speech'
    REASON_INAPPROPRIATE = 'inappropriate'
    REASON_IMPERSONATION = 'impersonation'
    REASON_OTHER = 'other'

    REASON_CHOICES = [
        (REASON_SPAM, 'Spam'),
        (REASON_HARASSMENT, 'Harassment or Bullying'),
        (REASON_HATE_SPEECH, 'Hate Speech'),
        (REASON_INAPPROPRIATE, 'Inappropriate Content'),
        (REASON_IMPERSONATION, 'Impersonation'),
        (REASON_OTHER, 'Other'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_REVIEWING = 'reviewing'
    STATUS_RESOLVED = 'resolved'
    STATUS_DISMISSED = 'dismissed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_REVIEWING, 'Under Review'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_DISMISSED, 'Dismissed'),
    ]

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    description = models.TextField(blank=True, help_text=_('Additional details about the report'))

    # Reported entities (only one should be set based on report_type)
    reported_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_against',
        null=True,
        blank=True
    )
    reported_post_id = models.IntegerField(null=True, blank=True, help_text=_('Post ID if reporting a post'))
    reported_comment_id = models.IntegerField(null=True, blank=True, help_text=_('Comment ID if reporting a comment'))

    # Moderation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='reports_reviewed',
        null=True,
        blank=True
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    moderator_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reports'
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        indexes = [
            models.Index(fields=['reporter', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['report_type', 'status']),
        ]

    def __str__(self):
        return f"Report({self.report_type}) by {self.reporter_id} - {self.reason}"


class PrivacySettings(models.Model):
    """
    User privacy settings
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='privacy_settings'
    )

    hide_avatar = models.BooleanField(
        default=False,
        help_text=_('Hide avatar from other users')
    )
    hide_online_status = models.BooleanField(
        default=False,
        help_text=_('Hide online status from other users')
    )
    allow_messages_from_strangers = models.BooleanField(
        default=True,
        help_text=_('Allow messages from users who are not following you')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'privacy_settings'
        verbose_name = _('Privacy Settings')
        verbose_name_plural = _('Privacy Settings')

    def __str__(self):
        return f"Privacy settings for {self.user.email}"
