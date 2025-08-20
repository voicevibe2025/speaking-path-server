"""
Serializers for speaking session models
"""
from rest_framework import serializers
from .models import PracticeSession, AudioRecording, SessionFeedback, RealTimeTranscript
from apps.authentication.serializers import UserSerializer


class SessionFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for session feedback
    """
    class Meta:
        model = SessionFeedback
        fields = [
            'id', 'feedback_type', 'feedback_text', 'severity',
            'error_word', 'correct_form', 'position_start', 'position_end',
            'recommendation', 'resource_links', 'cultural_note', 'created_at'
        ]
        read_only_fields = ['created_at']


class RealTimeTranscriptSerializer(serializers.ModelSerializer):
    """
    Serializer for real-time transcripts
    """
    class Meta:
        model = RealTimeTranscript
        fields = [
            'id', 'chunk_index', 'chunk_text', 'is_final',
            'start_time', 'end_time', 'confidence', 'created_at'
        ]
        read_only_fields = ['created_at']


class AudioRecordingSerializer(serializers.ModelSerializer):
    """
    Serializer for audio recordings
    """
    class Meta:
        model = AudioRecording
        fields = [
            'id', 'recording_id', 'sequence_number', 'recording_status',
            'audio_url', 'audio_format', 'duration_seconds', 'file_size_bytes',
            'sample_rate', 'transcription_text', 'transcription_confidence',
            'whisper_response', 'phonetic_analysis', 'prosody_analysis',
            'error_message', 'retry_count', 'created_at', 'processed_at'
        ]
        read_only_fields = ['recording_id', 'created_at']


class PracticeSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for practice sessions
    """
    user = UserSerializer(read_only=True)
    feedback_items = SessionFeedbackSerializer(many=True, read_only=True)
    audio_recordings = AudioRecordingSerializer(many=True, read_only=True)

    class Meta:
        model = PracticeSession
        fields = [
            'id', 'session_id', 'user', 'session_type', 'session_status',
            'scenario_id', 'scenario_title', 'scenario_description', 'scenario_difficulty',
            'target_language', 'target_proficiency', 'duration_seconds',
            'word_count', 'sentence_count', 'pronunciation_score', 'fluency_score',
            'grammar_score', 'vocabulary_score', 'overall_score',
            'ai_feedback', 'cultural_feedback', 'started_at', 'completed_at',
            'feedback_items', 'audio_recordings'
        ]
        read_only_fields = ['session_id', 'user', 'started_at']


class PracticeSessionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating practice sessions
    """
    class Meta:
        model = PracticeSession
        fields = [
            'session_type', 'scenario_id', 'scenario_title',
            'scenario_description', 'scenario_difficulty',
            'target_language', 'target_proficiency'
        ]

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PracticeSessionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating practice session scores and feedback
    """
    class Meta:
        model = PracticeSession
        fields = [
            'session_status', 'duration_seconds', 'word_count', 'sentence_count',
            'pronunciation_score', 'fluency_score', 'grammar_score',
            'vocabulary_score', 'overall_score', 'ai_feedback', 'cultural_feedback'
        ]


class SessionSummarySerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for session summaries
    """
    class Meta:
        model = PracticeSession
        fields = [
            'id', 'session_id', 'session_type', 'session_status',
            'scenario_title', 'duration_seconds', 'overall_score',
            'started_at', 'completed_at'
        ]


class SessionStatisticsSerializer(serializers.Serializer):
    """
    Serializer for session statistics
    """
    total_sessions = serializers.IntegerField()
    completed_sessions = serializers.IntegerField()
    total_practice_time = serializers.IntegerField()
    average_session_duration = serializers.FloatField()
    average_overall_score = serializers.FloatField()
    average_pronunciation_score = serializers.FloatField()
    average_fluency_score = serializers.FloatField()
    average_grammar_score = serializers.FloatField()
    average_vocabulary_score = serializers.FloatField()
    sessions_by_type = serializers.DictField()
    recent_sessions = SessionSummarySerializer(many=True)
    improvement_trend = serializers.DictField()
