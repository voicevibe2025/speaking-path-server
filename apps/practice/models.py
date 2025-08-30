from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()


class PracticePrompt(models.Model):
    """
    Practice prompt for speaking exercises
    """
    DIFFICULTY_LEVELS = [
        ('BEGINNER', 'BEGINNER'),
        ('INTERMEDIATE', 'INTERMEDIATE'),
        ('UPPER_INTERMEDIATE', 'UPPER_INTERMEDIATE'),
        ('ADVANCED', 'ADVANCED'),
        ('EXPERT', 'EXPERT'),
    ]

    SCENARIO_TYPES = [
        ('GENERAL', 'GENERAL'),
        ('BUSINESS', 'BUSINESS'),
        ('ACADEMIC', 'ACADEMIC'),
        ('SOCIAL', 'SOCIAL'),
        ('CULTURAL', 'CULTURAL'),
        ('TECHNICAL', 'TECHNICAL'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField(unique=True)
    category = models.CharField(max_length=100, db_index=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='BEGINNER')
    hints = models.JSONField(default=list, blank=True)
    target_duration = models.IntegerField(default=30)
    cultural_context = models.TextField(blank=True, null=True)
    scenario_type = models.CharField(max_length=20, choices=SCENARIO_TYPES, default='GENERAL')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'practice_prompts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"[{self.category}] {self.text[:40]}..."


class PracticeSubmission(models.Model):
    """
    Audio submission/evaluation session for a prompt
    """
    SESSION_STATUS = [
        ('PENDING', 'PENDING'),
        ('PROCESSING', 'PROCESSING'),
        ('EVALUATED', 'EVALUATED'),
        ('FAILED', 'FAILED'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practice_submissions')
    prompt = models.ForeignKey(PracticePrompt, on_delete=models.CASCADE, related_name='submissions')
    audio_url = models.TextField(blank=True)
    transcription = models.TextField(blank=True)
    evaluation = models.JSONField(default=dict, blank=True)
    score = models.FloatField(null=True, blank=True)
    duration = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'practice_submissions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Submission {self.id} ({self.status})"
