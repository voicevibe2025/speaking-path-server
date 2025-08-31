from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()


class Topic(models.Model):
    """
    Speaking Journey Topic with ordered sequence and material lines
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default="")
    material_lines = models.JSONField(default=list, blank=True)
    conversation_example = models.JSONField(default=list, blank=True)
    sequence = models.PositiveIntegerField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'speaking_journey_topics'
        verbose_name = _('Speaking Journey Topic')
        verbose_name_plural = _('Speaking Journey Topics')
        ordering = ['sequence']
        indexes = [
            models.Index(fields=['sequence']),
        ]

    def __str__(self):
        return f"{self.sequence}. {self.title}"


class TopicProgress(models.Model):
    """
    Per-user topic completion state
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topic_progress')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='progress_items')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'speaking_journey_topic_progress'
        unique_together = ('user', 'topic')
        verbose_name = _('Topic Progress')
        verbose_name_plural = _('Topic Progress')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['topic']),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.topic_id} - {'completed' if self.completed else 'pending'}"


class PhraseProgress(models.Model):
    """
    Per-user phrase learning progress within each topic
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phrase_progress')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='phrase_progress_items')
    current_phrase_index = models.PositiveIntegerField(default=0)  # Which phrase user is currently on (0-based)
    completed_phrases = models.JSONField(default=list, blank=True)  # List of completed phrase indices
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'speaking_journey_phrase_progress'
        unique_together = ('user', 'topic')
        verbose_name = _('Phrase Progress')
        verbose_name_plural = _('Phrase Progress')
        indexes = [
            models.Index(fields=['user', 'topic']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.topic.title} - phrase {self.current_phrase_index}"

    def is_phrase_completed(self, phrase_index):
        """Check if a specific phrase has been completed"""
        return phrase_index in (self.completed_phrases or [])

    def mark_phrase_completed(self, phrase_index):
        """Mark a phrase as completed and advance to next if needed"""
        completed = self.completed_phrases or []
        if phrase_index not in completed:
            completed.append(phrase_index)
            self.completed_phrases = completed

            # Advance to next phrase if this was the current one
            if phrase_index == self.current_phrase_index:
                self.current_phrase_index = phrase_index + 1

            self.save(update_fields=['completed_phrases', 'current_phrase_index'])

    def reset_progress(self):
        """Reset phrase progress back to beginning"""
        self.current_phrase_index = 0
        self.completed_phrases = []
        self.save(update_fields=['current_phrase_index', 'completed_phrases'])

    @property
    def is_all_phrases_completed(self):
        """Check if all phrases in the topic are completed"""
        topic_phrase_count = len(self.topic.material_lines or [])
        completed_count = len(self.completed_phrases or [])
        return completed_count >= topic_phrase_count and topic_phrase_count > 0


class UserProfile(models.Model):
    """
    User profile for Speaking Journey tracking
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='speaking_journey_profile')
    last_visited_topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    first_visit = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'speaking_journey_user_profiles'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return f"{self.user.username} - Journey Profile"
