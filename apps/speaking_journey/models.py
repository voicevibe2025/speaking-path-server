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


def user_phrase_audio_upload_to(instance, filename):
    """Build a storage path for user phrase recordings.
    Example: speaking_journey/<user_id>/<topic_id>/phrase_<idx>/<uuid>.<ext>
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else 'm4a'
    return f"speaking_journey/{instance.user_id}/{instance.topic_id}/phrase_{instance.phrase_index}/{uuid.uuid4()}.{ext}"


class UserPhraseRecording(models.Model):
    """
    Per-user stored recordings for Speaking Journey phrases.
    We store the audio file in MEDIA_ROOT via default storage and link it to the user/topic/phrase.
    Multiple attempts per phrase are allowed.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journey_phrase_recordings')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='phrase_recordings')
    phrase_index = models.PositiveIntegerField()

    # Audio file persisted to storage
    audio_file = models.FileField(upload_to=user_phrase_audio_upload_to)

    # Metadata and results
    transcription = models.TextField(blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'speaking_journey_user_phrase_recordings'
        verbose_name = _('User Phrase Recording')
        verbose_name_plural = _('User Phrase Recordings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'topic']),
            models.Index(fields=['topic', 'phrase_index']),
            models.Index(fields=['user', 'topic', 'phrase_index']),
        ]

    def __str__(self):
        return f"Recording {self.id} - {self.user_id} - {self.topic_id} - phrase {self.phrase_index}"
