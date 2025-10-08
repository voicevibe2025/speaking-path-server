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
    # List of key vocabulary words for this topic (e.g., ["arrival", "departure", ...])
    vocabulary = models.JSONField(default=list, blank=True)
    # List of fluency practice prompts for this topic
    fluency_practice_prompt = models.JSONField(default=list, blank=True)
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
    # Per-mode completion flags (all must be True to consider the topic fully completed)
    pronunciation_completed = models.BooleanField(default=False)
    fluency_completed = models.BooleanField(default=False)
    vocabulary_completed = models.BooleanField(default=False)
    listening_completed = models.BooleanField(default=False)
    grammar_completed = models.BooleanField(default=False)
    # Sum of latest accuracies (0-100) across all phrases in this topic
    # This accumulates as the user practices phrases and is finalized when all phrases are done
    pronunciation_total_score = models.IntegerField(default=0)
    # Fluency scoring across up to 3 prompts per topic
    fluency_total_score = models.IntegerField(default=0)
    # Vocabulary total score across generated quiz sessions (latest completed)
    vocabulary_total_score = models.IntegerField(default=0)
    # Listening total score across generated listening quiz sessions (latest completed, normalized 0-100)
    listening_total_score = models.IntegerField(default=0)
    # Per-prompt scores recorded in order; length up to number of prompts (typically 3)
    fluency_prompt_scores = models.JSONField(default=list, blank=True)
    # Conversation practice (bonus mode) aggregate score and completion flag
    # Not required for topic unlocking; used for tracking and XP.
    conversation_total_score = models.IntegerField(default=0)
    conversation_completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'speaking_journey_topic_progress'
        unique_together = ('user', 'topic')
        verbose_name = _('Topic Progress')
        verbose_name_plural = _('Topic Progress')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['topic']),
        ]

    @property
    def all_modes_completed(self):
        """Return True only if core practice modes are completed.
        Listening and Grammar are optional bonus practices that don't block unlocking.
        """
        return (
            self.pronunciation_completed and
            self.fluency_completed and
            self.vocabulary_completed
        )

    def __str__(self):
        return f"{self.user_id} - {self.topic_id} - {'completed' if self.completed else 'pending'}"


class VocabularyPracticeSession(models.Model):
    """
    Track per-user Vocabulary practice session for a topic.
    Stores generated questions (definition + options) to ensure consistent
    validation and XP awarding per session.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vocab_sessions')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='vocab_sessions')
    # Public session identifier returned to clients
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Persist the full question set for this session as a list of dicts:
    # [{ 'id': '<uuid>', 'word': 'arrival', 'definition': '...', 'options': ['..','..','..','..'], 'answered': False, 'correct': None }]
    questions = models.JSONField(default=list, blank=True)
    total_questions = models.IntegerField(default=0)
    current_index = models.IntegerField(default=0)
    correct_count = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'speaking_journey_vocab_sessions'
        verbose_name = _('Vocabulary Practice Session')
        verbose_name_plural = _('Vocabulary Practice Sessions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'topic']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"VocabSession {self.session_id} - {self.user_id} - {self.topic_id}"


class ListeningPracticeSession(models.Model):
    """
    Track per-user Listening practice session for a topic.
    Stores generated MCQ questions (audio prompt is generated client-side via TTS).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listening_sessions')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='listening_sessions')
    # Public session identifier returned to clients
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Persist the full question set for this session as a list of dicts:
    # [{ 'id': '<uuid>', 'question': '...', 'options': ['..','..','..','..'], 'answer': '<exact correct option>', 'answered': False, 'correct': None }]
    questions = models.JSONField(default=list, blank=True)
    total_questions = models.IntegerField(default=0)
    current_index = models.IntegerField(default=0)
    correct_count = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'speaking_journey_listening_sessions'
        verbose_name = _('Listening Practice Session')
        verbose_name_plural = _('Listening Practice Sessions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'topic']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"ListeningSession {self.session_id} - {self.user_id} - {self.topic_id}"


class GrammarPracticeSession(models.Model):
    """
    Track per-user Grammar practice session for a topic.
    Stores AI-generated fill-in-the-blank grammar questions with 4 options each.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grammar_sessions')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='grammar_sessions')
    # Public session identifier returned to clients
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Persist the full question set for this session as a list of dicts:
    # [{ 'id': '<uuid>', 'sentence': 'I ____ to the store yesterday.', 'options': ['go','went','gone','going'], 'answer': 'went', 'answered': False, 'correct': None }]
    questions = models.JSONField(default=list, blank=True)
    total_questions = models.IntegerField(default=0)
    current_index = models.IntegerField(default=0)
    correct_count = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'speaking_journey_grammar_sessions'
        verbose_name = _('Grammar Practice Session')
        verbose_name_plural = _('Grammar Practice Sessions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'topic']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"GrammarSession {self.session_id} - {self.user_id} - {self.topic_id}"


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


def user_conversation_audio_upload_to(instance, filename):
    """Build a storage path for user conversation turn recordings.
    Example: speaking_journey/<user_id>/<topic_id>/conversation_turn_<idx>/<uuid>.<ext>
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else 'm4a'
    return (
        f"speaking_journey/{instance.user_id}/{instance.topic_id}/conversation_turn_"
        f"{instance.turn_index}/{uuid.uuid4()}.{ext}"
    )


class UserConversationRecording(models.Model):
    """Per-user stored recordings for Conversation Practice turns.
    Stored separately from phrase recordings to keep histories distinct.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journey_conversation_recordings')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='conversation_recordings')
    turn_index = models.PositiveIntegerField()
    # Optional: which side the user chose (e.g., "A" or "B"), not strictly required for scoring
    role = models.CharField(max_length=8, blank=True, default="")

    # Audio file persisted to storage
    audio_file = models.FileField(upload_to=user_conversation_audio_upload_to)

    # Metadata and results
    transcription = models.TextField(blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'speaking_journey_user_conversation_recordings'
        verbose_name = _('User Conversation Recording')
        verbose_name_plural = _('User Conversation Recordings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'topic']),
            models.Index(fields=['topic', 'turn_index']),
            models.Index(fields=['user', 'topic', 'turn_index']),
        ]

    def __str__(self):
        return f"ConversationRec {self.id} - {self.user_id} - {self.topic_id} - turn {self.turn_index}"
