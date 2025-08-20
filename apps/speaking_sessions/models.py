"""
Speaking session models for VoiceVibe
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class PracticeSession(models.Model):
    """
    Model for speaking practice sessions
    """
    SESSION_STATUS = [
        ('initiated', _('Initiated')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('error', _('Error')),
    ]

    SESSION_TYPES = [
        ('free_practice', _('Free Practice')),
        ('scenario_based', _('Scenario Based')),
        ('pronunciation', _('Pronunciation Practice')),
        ('conversation', _('Conversation')),
        ('vocabulary', _('Vocabulary Practice')),
        ('grammar', _('Grammar Practice')),
    ]

    # Session identification
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practice_sessions')

    # Session details
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='free_practice')
    session_status = models.CharField(max_length=15, choices=SESSION_STATUS, default='initiated')

    # Scenario information
    scenario_id = models.CharField(max_length=100, blank=True)
    scenario_title = models.CharField(max_length=200, blank=True)
    scenario_description = models.TextField(blank=True)
    scenario_difficulty = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )

    # Target language and proficiency
    target_language = models.CharField(max_length=10, default='en')
    target_proficiency = models.CharField(max_length=20, blank=True)

    # Session metrics
    duration_seconds = models.IntegerField(default=0)
    word_count = models.IntegerField(default=0)
    sentence_count = models.IntegerField(default=0)

    # Scores (0-100)
    pronunciation_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    fluency_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    grammar_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    vocabulary_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    overall_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])

    # AI Feedback
    ai_feedback = models.JSONField(default=dict, blank=True)
    cultural_feedback = models.JSONField(default=dict, blank=True)

    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'practice_sessions'
        verbose_name = _('Practice Session')
        verbose_name_plural = _('Practice Sessions')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"Session {self.session_id} - {self.user.email}"


class AudioRecording(models.Model):
    """
    Model for audio recordings in practice sessions
    """
    RECORDING_STATUS = [
        ('uploading', _('Uploading')),
        ('uploaded', _('Uploaded')),
        ('processing', _('Processing')),
        ('transcribed', _('Transcribed')),
        ('analyzed', _('Analyzed')),
        ('error', _('Error')),
    ]

    # Recording identification
    recording_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name='audio_recordings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audio_recordings')

    # Recording details
    sequence_number = models.IntegerField(default=1)  # Order within session
    recording_status = models.CharField(max_length=15, choices=RECORDING_STATUS, default='uploading')

    # Audio file information
    audio_url = models.URLField(blank=True)
    audio_format = models.CharField(max_length=10, default='webm')
    duration_seconds = models.FloatField(default=0)
    file_size_bytes = models.IntegerField(default=0)
    sample_rate = models.IntegerField(default=16000)

    # Transcription
    transcription_text = models.TextField(blank=True)
    transcription_confidence = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(1)])
    whisper_response = models.JSONField(default=dict, blank=True)

    # Analysis results
    phonetic_analysis = models.JSONField(default=dict, blank=True)
    prosody_analysis = models.JSONField(default=dict, blank=True)

    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'audio_recordings'
        verbose_name = _('Audio Recording')
        verbose_name_plural = _('Audio Recordings')
        ordering = ['session', 'sequence_number']
        unique_together = ['session', 'sequence_number']
        indexes = [
            models.Index(fields=['recording_id']),
            models.Index(fields=['session', 'sequence_number']),
        ]

    def __str__(self):
        return f"Recording {self.sequence_number} - Session {self.session.session_id}"


class SessionFeedback(models.Model):
    """
    Detailed feedback for practice sessions
    """
    FEEDBACK_TYPES = [
        ('pronunciation', _('Pronunciation')),
        ('grammar', _('Grammar')),
        ('vocabulary', _('Vocabulary')),
        ('fluency', _('Fluency')),
        ('cultural', _('Cultural')),
        ('pragmatic', _('Pragmatic')),
    ]

    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name='feedback_items')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)

    # Feedback content
    feedback_text = models.TextField()
    severity = models.CharField(
        max_length=10,
        choices=[
            ('info', _('Info')),
            ('minor', _('Minor')),
            ('moderate', _('Moderate')),
            ('major', _('Major')),
        ],
        default='info'
    )

    # Specific error/issue details
    error_word = models.CharField(max_length=100, blank=True)
    correct_form = models.CharField(max_length=100, blank=True)
    position_start = models.IntegerField(null=True, blank=True)
    position_end = models.IntegerField(null=True, blank=True)

    # Recommendations
    recommendation = models.TextField(blank=True)
    resource_links = models.JSONField(default=list, blank=True)

    # Cultural context (for Indonesian learners)
    cultural_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_feedback'
        verbose_name = _('Session Feedback')
        verbose_name_plural = _('Session Feedback Items')
        ordering = ['session', 'feedback_type']

    def __str__(self):
        return f"{self.feedback_type} feedback for {self.session.session_id}"


class RealTimeTranscript(models.Model):
    """
    Real-time transcription chunks for WebSocket streaming
    """
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name='realtime_transcripts')

    # Chunk information
    chunk_index = models.IntegerField()
    chunk_text = models.TextField()
    is_final = models.BooleanField(default=False)

    # Timing information
    start_time = models.FloatField()  # seconds from session start
    end_time = models.FloatField()

    # Confidence
    confidence = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'realtime_transcripts'
        verbose_name = _('Real-time Transcript')
        verbose_name_plural = _('Real-time Transcripts')
        ordering = ['session', 'chunk_index']
        unique_together = ['session', 'chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} - Session {self.session.session_id}"
