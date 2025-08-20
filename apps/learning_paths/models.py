"""
Models for Learning Paths
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class LearningPath(models.Model):
    """
    Personalized learning path for a user
    """
    PATH_TYPES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('business', 'Business English'),
        ('academic', 'Academic English'),
        ('conversational', 'Conversational'),
        ('exam_prep', 'Exam Preparation'),
        ('custom', 'Custom Path')
    )

    DIFFICULTY_LEVELS = (
        ('A1', 'A1 - Beginner'),
        ('A2', 'A2 - Elementary'),
        ('B1', 'B1 - Intermediate'),
        ('B2', 'B2 - Upper Intermediate'),
        ('C1', 'C1 - Advanced'),
        ('C2', 'C2 - Proficiency')
    )

    path_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_paths')

    # Path details
    name = models.CharField(max_length=200)
    description = models.TextField()
    path_type = models.CharField(max_length=20, choices=PATH_TYPES)
    difficulty_level = models.CharField(max_length=5, choices=DIFFICULTY_LEVELS)

    # Goals and timeline
    learning_goal = models.TextField(help_text="Main objective of this learning path")
    estimated_duration_weeks = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(52)]
    )
    target_proficiency = models.CharField(max_length=5, choices=DIFFICULTY_LEVELS)

    # Progress tracking
    is_active = models.BooleanField(default=True)
    progress_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    current_module_index = models.IntegerField(default=0)

    # Personalization
    focus_areas = models.JSONField(default=list, help_text="List of focus areas like pronunciation, grammar, etc.")
    cultural_context = models.JSONField(default=dict, help_text="Cultural adaptation parameters")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['path_type', 'difficulty_level']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class LearningModule(models.Model):
    """
    Individual module within a learning path
    """
    MODULE_TYPES = (
        ('pronunciation', 'Pronunciation'),
        ('grammar', 'Grammar'),
        ('vocabulary', 'Vocabulary'),
        ('fluency', 'Fluency'),
        ('listening', 'Listening'),
        ('cultural', 'Cultural Context'),
        ('scenario', 'Scenario Practice'),
        ('assessment', 'Assessment')
    )

    module_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='modules')

    # Module details
    name = models.CharField(max_length=200)
    description = models.TextField()
    module_type = models.CharField(max_length=20, choices=MODULE_TYPES)
    order_index = models.IntegerField(help_text="Order of module in the path")

    # Content
    learning_objectives = models.JSONField(default=list)
    prerequisites = models.JSONField(default=list, help_text="List of prerequisite module IDs")
    content = models.JSONField(default=dict, help_text="Module content and resources")

    # Requirements
    estimated_duration_minutes = models.IntegerField(validators=[MinValueValidator(5)])
    minimum_score = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum score to pass the module"
    )
    max_attempts = models.IntegerField(default=3, validators=[MinValueValidator(1)])

    # Progress
    is_locked = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['learning_path', 'order_index']
        unique_together = [['learning_path', 'order_index']]

    def __str__(self):
        return f"{self.learning_path.name} - {self.name}"


class ModuleActivity(models.Model):
    """
    Individual learning activity within a module
    """
    ACTIVITY_TYPES = (
        ('lesson', 'Lesson'),
        ('practice', 'Practice Exercise'),
        ('quiz', 'Quiz'),
        ('speaking', 'Speaking Practice'),
        ('listening', 'Listening Exercise'),
        ('roleplay', 'Role Play'),
        ('assessment', 'Assessment')
    )

    activity_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    module = models.ForeignKey(LearningModule, on_delete=models.CASCADE, related_name='activities')

    # Activity details
    name = models.CharField(max_length=200)
    description = models.TextField()
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    order_index = models.IntegerField()

    # Content
    instructions = models.TextField()
    content = models.JSONField(default=dict, help_text="Activity content, questions, scenarios, etc.")
    resources = models.JSONField(default=list, help_text="URLs to resources, materials")

    # Requirements
    estimated_duration_minutes = models.IntegerField(validators=[MinValueValidator(1)])
    points = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    passing_score = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # AI Integration
    requires_ai_evaluation = models.BooleanField(default=False)
    ai_evaluation_criteria = models.JSONField(default=dict, null=True, blank=True)

    # Cultural adaptation
    cultural_notes = models.TextField(null=True, blank=True)
    indonesian_context = models.JSONField(default=dict, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['module', 'order_index']
        unique_together = [['module', 'order_index']]

    def __str__(self):
        return f"{self.module.name} - {self.name}"


class UserProgress(models.Model):
    """
    Track user progress through learning paths and modules
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_progress')
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='user_progress')
    module = models.ForeignKey(LearningModule, on_delete=models.CASCADE, related_name='user_progress', null=True, blank=True)
    activity = models.ForeignKey(ModuleActivity, on_delete=models.CASCADE, related_name='user_progress', null=True, blank=True)

    # Progress details
    status = models.CharField(
        max_length=20,
        choices=(
            ('not_started', 'Not Started'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('skipped', 'Skipped')
        ),
        default='not_started'
    )

    # Performance
    score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    attempts = models.IntegerField(default=0)
    time_spent_minutes = models.IntegerField(default=0)

    # Detailed results
    results = models.JSONField(default=dict, help_text="Detailed results, answers, feedback")
    ai_feedback = models.JSONField(default=dict, null=True, blank=True)

    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_attempt_at']
        indexes = [
            models.Index(fields=['user', 'learning_path']),
            models.Index(fields=['user', 'module']),
        ]
        unique_together = [['user', 'learning_path', 'module', 'activity']]

    def __str__(self):
        return f"{self.user.username} - {self.learning_path.name} Progress"


class Milestone(models.Model):
    """
    Learning milestones and achievements within paths
    """
    MILESTONE_TYPES = (
        ('module_completion', 'Module Completion'),
        ('path_completion', 'Path Completion'),
        ('score_achievement', 'Score Achievement'),
        ('streak', 'Practice Streak'),
        ('proficiency', 'Proficiency Level'),
        ('special', 'Special Achievement')
    )

    milestone_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='milestones', null=True, blank=True)

    # Milestone details
    name = models.CharField(max_length=200)
    description = models.TextField()
    milestone_type = models.CharField(max_length=20, choices=MILESTONE_TYPES)

    # Requirements
    requirements = models.JSONField(default=dict, help_text="Conditions to achieve milestone")
    points = models.IntegerField(default=100)

    # Visual elements
    icon = models.CharField(max_length=50, null=True, blank=True)
    badge_image = models.URLField(null=True, blank=True)

    # Cultural elements for Indonesian context
    cultural_reference = models.CharField(max_length=100, null=True, blank=True, help_text="e.g., Wayang character, Batik pattern")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['learning_path', 'name']

    def __str__(self):
        return self.name


class UserMilestone(models.Model):
    """
    Track user's achieved milestones
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achieved_milestones')
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='user_achievements')
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, null=True, blank=True)

    # Achievement details
    achieved_at = models.DateTimeField(auto_now_add=True)
    achievement_data = models.JSONField(default=dict, help_text="Data related to achievement")

    class Meta:
        ordering = ['-achieved_at']
        unique_together = [['user', 'milestone']]

    def __str__(self):
        return f"{self.user.username} - {self.milestone.name}"
