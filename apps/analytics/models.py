"""
Analytics models for tracking user progress and performance
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class UserAnalytics(models.Model):
    """
    Aggregated analytics for user performance
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='analytics'
    )

    # Overall Progress Metrics
    total_practice_time_minutes = models.IntegerField(default=0)
    total_sessions_completed = models.IntegerField(default=0)
    average_session_duration_minutes = models.FloatField(default=0.0)
    current_streak_days = models.IntegerField(default=0)
    longest_streak_days = models.IntegerField(default=0)
    last_practice_date = models.DateField(null=True, blank=True)

    # Performance Metrics (0-100 scale)
    overall_proficiency_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    pronunciation_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    fluency_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    vocabulary_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    grammar_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    coherence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Improvement Tracking
    initial_proficiency_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    improvement_rate = models.FloatField(default=0.0)  # percentage per week

    # Learning Pattern Metrics
    preferred_practice_time = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Morning (6am-12pm)'),
            ('afternoon', 'Afternoon (12pm-6pm)'),
            ('evening', 'Evening (6pm-10pm)'),
            ('night', 'Night (10pm-6am)'),
        ],
        blank=True
    )
    average_words_per_minute = models.FloatField(default=0.0)
    vocabulary_size_estimate = models.IntegerField(default=0)

    # Engagement Metrics
    scenarios_completed = models.IntegerField(default=0)
    achievements_earned = models.IntegerField(default=0)
    feedback_interactions = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Analytics"
        verbose_name_plural = "User Analytics"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Analytics for {self.user.email}"

    def calculate_improvement_rate(self):
        """Calculate weekly improvement rate"""
        if not self.initial_proficiency_score:
            return 0.0

        days_active = (timezone.now().date() - self.created_at.date()).days
        if days_active < 7:
            return 0.0

        weeks_active = days_active / 7
        improvement = self.overall_proficiency_score - self.initial_proficiency_score
        return improvement / weeks_active if weeks_active > 0 else 0.0


class SessionAnalytics(models.Model):
    """
    Analytics for individual practice sessions
    """
    analytics_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='session_analytics'
    )
    session = models.ForeignKey(
        'speaking_sessions.PracticeSession',
        on_delete=models.CASCADE,
        related_name='analytics',
        null=True,
        blank=True
    )

    # Session Details
    session_type = models.CharField(
        max_length=30,
        choices=[
            ('free_practice', 'Free Practice'),
            ('scenario_based', 'Scenario Based'),
            ('assessment', 'Assessment'),
            ('lesson', 'Lesson'),
            ('conversation', 'Conversation'),
        ]
    )
    scenario_id = models.CharField(max_length=50, blank=True)
    difficulty_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    # Time Metrics
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_seconds = models.IntegerField()
    speaking_time_seconds = models.IntegerField(default=0)
    silence_time_seconds = models.IntegerField(default=0)

    # Performance Scores (0-100)
    overall_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    pronunciation_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    fluency_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    vocabulary_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    grammar_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    coherence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Speech Metrics
    total_words = models.IntegerField(default=0)
    unique_words = models.IntegerField(default=0)
    words_per_minute = models.FloatField(default=0.0)
    filler_words_count = models.IntegerField(default=0)

    # Error Analysis
    pronunciation_errors_count = models.IntegerField(default=0)
    grammar_errors_count = models.IntegerField(default=0)
    vocabulary_errors_count = models.IntegerField(default=0)

    # Common Errors (JSON field for flexibility)
    common_errors = models.JSONField(default=dict)
    # Structure: {
    #     'pronunciation': ['word1', 'word2'],
    #     'grammar': ['error_type1', 'error_type2'],
    #     'vocabulary': ['misused_word1', 'misused_word2']
    # }

    # User Behavior
    pause_count = models.IntegerField(default=0)
    retry_count = models.IntegerField(default=0)
    hint_requests = models.IntegerField(default=0)

    # Completion Status
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Session Analytics"
        verbose_name_plural = "Session Analytics"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_type', '-created_at']),
        ]

    def __str__(self):
        return f"Session {self.analytics_id} - {self.user.email}"

    def calculate_duration(self):
        """Calculate session duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0


class LearningProgress(models.Model):
    """
    Track detailed learning progress over time
    """
    progress_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analytics_progress'
    )

    # Time Period
    date = models.DateField()
    week_number = models.IntegerField()  # Week of the year
    month = models.IntegerField()  # Month number
    year = models.IntegerField()

    # Daily Metrics
    practice_time_minutes = models.IntegerField(default=0)
    sessions_count = models.IntegerField(default=0)
    words_practiced = models.IntegerField(default=0)
    scenarios_completed = models.IntegerField(default=0)

    # Performance Averages for the Day
    avg_pronunciation_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    avg_fluency_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    avg_vocabulary_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    avg_grammar_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    avg_coherence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Skill Progress
    skills_improved = models.JSONField(default=list)
    # ['pronunciation', 'fluency', 'vocabulary', etc.]

    # Goal Tracking
    daily_goal_minutes = models.IntegerField(default=30)
    goal_achieved = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Learning Progress"
        verbose_name_plural = "Learning Progress"
        ordering = ['-date']
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['week_number', 'year']),
        ]

    def __str__(self):
        return f"Progress for {self.user.email} on {self.date}"


class ErrorPattern(models.Model):
    """
    Track recurring error patterns for targeted improvement
    """
    pattern_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='error_patterns'
    )

    # Error Details
    error_type = models.CharField(
        max_length=30,
        choices=[
            ('pronunciation', 'Pronunciation'),
            ('grammar', 'Grammar'),
            ('vocabulary', 'Vocabulary'),
            ('fluency', 'Fluency'),
            ('coherence', 'Coherence'),
            ('cultural', 'Cultural'),
        ]
    )
    error_pattern = models.CharField(max_length=200)
    error_description = models.TextField()

    # Examples
    example_errors = models.JSONField(default=list)
    # ['error1', 'error2', 'error3']
    correct_forms = models.JSONField(default=list)
    # ['correct1', 'correct2', 'correct3']

    # Frequency and Impact
    occurrence_count = models.IntegerField(default=1)
    last_occurrence = models.DateTimeField()
    severity_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    impact_on_communication = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )

    # Improvement Tracking
    is_improving = models.BooleanField(default=False)
    improvement_rate = models.FloatField(default=0.0)  # percentage
    targeted_exercises = models.JSONField(default=list)
    # ['exercise_id1', 'exercise_id2']

    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_date = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Error Pattern"
        verbose_name_plural = "Error Patterns"
        ordering = ['-occurrence_count', '-last_occurrence']
        indexes = [
            models.Index(fields=['user', 'error_type', '-occurrence_count']),
        ]

    def __str__(self):
        return f"{self.error_type} pattern for {self.user.email}: {self.error_pattern}"


class SkillAssessment(models.Model):
    """
    Periodic skill assessments and benchmarks
    """
    assessment_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='skill_assessments'
    )

    # Assessment Type
    assessment_type = models.CharField(
        max_length=30,
        choices=[
            ('initial', 'Initial Assessment'),
            ('weekly', 'Weekly Assessment'),
            ('monthly', 'Monthly Assessment'),
            ('milestone', 'Milestone Assessment'),
            ('final', 'Final Assessment'),
        ]
    )
    assessment_date = models.DateTimeField()

    # Skill Scores (0-100)
    pronunciation_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    fluency_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    vocabulary_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    grammar_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    coherence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    cultural_appropriateness_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Overall Assessment
    overall_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    proficiency_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('elementary', 'Elementary'),
            ('intermediate', 'Intermediate'),
            ('upper_intermediate', 'Upper Intermediate'),
            ('advanced', 'Advanced'),
            ('proficient', 'Proficient'),
        ]
    )

    # Detailed Feedback
    strengths = models.JSONField(default=list)
    # ['pronunciation', 'vocabulary', etc.]
    weaknesses = models.JSONField(default=list)
    # ['grammar', 'fluency', etc.]
    recommendations = models.JSONField(default=list)
    # ['Focus on grammar exercises', 'Practice speaking more', etc.]

    # Comparison with Previous
    improvement_from_last = models.FloatField(default=0.0)  # percentage

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Skill Assessment"
        verbose_name_plural = "Skill Assessments"
        ordering = ['-assessment_date']
        indexes = [
            models.Index(fields=['user', '-assessment_date']),
            models.Index(fields=['assessment_type', '-assessment_date']),
        ]

    def __str__(self):
        return f"{self.assessment_type} for {self.user.email} on {self.assessment_date}"

    def calculate_overall_score(self):
        """Calculate weighted overall score"""
        weights = {
            'pronunciation': 0.25,
            'fluency': 0.20,
            'vocabulary': 0.20,
            'grammar': 0.20,
            'coherence': 0.10,
            'cultural': 0.05
        }

        total = (
            self.pronunciation_score * weights['pronunciation'] +
            self.fluency_score * weights['fluency'] +
            self.vocabulary_score * weights['vocabulary'] +
            self.grammar_score * weights['grammar'] +
            self.coherence_score * weights['coherence'] +
            self.cultural_appropriateness_score * weights['cultural']
        )

        return round(total, 2)


class ChatModeUsage(models.Model):
    """
    Track usage of Text vs Voice chat modes with Vivi
    """
    usage_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_mode_usage'
    )
    
    # Chat Mode
    mode = models.CharField(
        max_length=10,
        choices=[
            ('text', 'Text Chat'),
            ('voice', 'Voice Chat'),
        ]
    )
    
    # Session Details
    session_id = models.UUIDField(default=uuid.uuid4)  # Group related chat interactions
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    
    # Usage Metrics
    message_count = models.IntegerField(default=0)  # Number of messages/turns
    is_active = models.BooleanField(default=True)  # Currently active session
    
    # Metadata
    device_info = models.CharField(max_length=100, blank=True)  # Optional device/platform info
    app_version = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Chat Mode Usage"
        verbose_name_plural = "Chat Mode Usages"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['mode', '-started_at']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_mode_display()} - {self.started_at}"
    
    def calculate_duration(self):
        """Calculate session duration in seconds"""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        elif not self.is_active:
            return self.duration_seconds
        else:
            # Still active, calculate current duration
            return (timezone.now() - self.started_at).total_seconds()
    
    def end_session(self):
        """Mark session as ended"""
        if self.is_active:
            self.ended_at = timezone.now()
            self.duration_seconds = int(self.calculate_duration())
            self.is_active = False
            self.save()
