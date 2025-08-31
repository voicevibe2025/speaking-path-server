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
