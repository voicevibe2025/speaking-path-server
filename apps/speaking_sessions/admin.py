"""
Admin configuration for speaking session models
"""
from django.contrib import admin
from .models import PracticeSession, AudioRecording, SessionFeedback, RealTimeTranscript


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    """
    Admin for practice sessions
    """
    list_display = (
        'session_id', 'user', 'session_type', 'session_status',
        'scenario_title', 'overall_score', 'started_at', 'completed_at'
    )
    list_filter = (
        'session_status', 'session_type', 'target_language',
        'started_at', 'completed_at'
    )
    search_fields = (
        'session_id', 'user__email', 'user__username',
        'scenario_title', 'scenario_description'
    )
    ordering = ('-started_at',)
    readonly_fields = ('session_id', 'started_at')

    fieldsets = (
        ('Session Info', {
            'fields': ('session_id', 'user', 'session_type', 'session_status')
        }),
        ('Scenario', {
            'fields': (
                'scenario_id', 'scenario_title', 'scenario_description',
                'scenario_difficulty'
            )
        }),
        ('Language Settings', {
            'fields': ('target_language', 'target_proficiency')
        }),
        ('Metrics', {
            'fields': (
                'duration_seconds', 'word_count', 'sentence_count'
            )
        }),
        ('Scores', {
            'fields': (
                'pronunciation_score', 'fluency_score', 'grammar_score',
                'vocabulary_score', 'overall_score'
            )
        }),
        ('AI Feedback', {
            'fields': ('ai_feedback', 'cultural_feedback'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at')
        })
    )


@admin.register(AudioRecording)
class AudioRecordingAdmin(admin.ModelAdmin):
    """
    Admin for audio recordings
    """
    list_display = (
        'recording_id', 'session', 'user', 'sequence_number',
        'recording_status', 'duration_seconds', 'created_at'
    )
    list_filter = (
        'recording_status', 'audio_format', 'created_at'
    )
    search_fields = (
        'recording_id', 'session__session_id', 'user__email',
        'transcription_text'
    )
    ordering = ('session', 'sequence_number')
    readonly_fields = ('recording_id', 'created_at')

    fieldsets = (
        ('Recording Info', {
            'fields': (
                'recording_id', 'session', 'user', 'sequence_number',
                'recording_status'
            )
        }),
        ('Audio Data', {
            'fields': (
                'audio_url', 'audio_format', 'duration_seconds',
                'file_size_bytes', 'sample_rate'
            )
        }),
        ('Transcription', {
            'fields': (
                'transcription_text', 'transcription_confidence',
                'whisper_response'
            ),
            'classes': ('collapse',)
        }),
        ('Analysis', {
            'fields': ('phonetic_analysis', 'prosody_analysis'),
            'classes': ('collapse',)
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at')
        })
    )


@admin.register(SessionFeedback)
class SessionFeedbackAdmin(admin.ModelAdmin):
    """
    Admin for session feedback
    """
    list_display = (
        'session', 'feedback_type', 'severity',
        'error_word', 'correct_form', 'created_at'
    )
    list_filter = (
        'feedback_type', 'severity', 'created_at'
    )
    search_fields = (
        'session__session_id', 'feedback_text',
        'error_word', 'recommendation'
    )
    ordering = ('session', 'feedback_type', '-severity')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Feedback Info', {
            'fields': ('session', 'feedback_type', 'severity')
        }),
        ('Content', {
            'fields': ('feedback_text',)
        }),
        ('Error Details', {
            'fields': (
                'error_word', 'correct_form',
                'position_start', 'position_end'
            )
        }),
        ('Recommendations', {
            'fields': ('recommendation', 'resource_links')
        }),
        ('Cultural Context', {
            'fields': ('cultural_note',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )


@admin.register(RealTimeTranscript)
class RealTimeTranscriptAdmin(admin.ModelAdmin):
    """
    Admin for real-time transcripts
    """
    list_display = (
        'session', 'chunk_index', 'chunk_text',
        'is_final', 'confidence', 'created_at'
    )
    list_filter = ('is_final', 'created_at')
    search_fields = ('session__session_id', 'chunk_text')
    ordering = ('session', 'chunk_index')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Transcript Info', {
            'fields': ('session', 'chunk_index', 'is_final')
        }),
        ('Content', {
            'fields': ('chunk_text',)
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Quality', {
            'fields': ('confidence',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )
