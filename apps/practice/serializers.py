from rest_framework import serializers
from .models import PracticePrompt, PracticeSubmission


class PracticePromptSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex_verbose', read_only=True)
    targetDuration = serializers.IntegerField(source='target_duration')
    culturalContext = serializers.CharField(source='cultural_context', allow_null=True, required=False)
    scenarioType = serializers.CharField(source='scenario_type')

    class Meta:
        model = PracticePrompt
        fields = [
            'id', 'text', 'category', 'difficulty', 'hints',
            'targetDuration', 'culturalContext', 'scenarioType'
        ]


class SubmissionResultSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    score = serializers.FloatField()
    feedback = serializers.CharField()


class EvaluationScoreSerializer(serializers.Serializer):
    score = serializers.FloatField()
    level = serializers.CharField()
    feedback = serializers.CharField()


class PhoneticErrorSerializer(serializers.Serializer):
    word = serializers.CharField()
    expected = serializers.CharField()
    actual = serializers.CharField()
    timestamp = serializers.FloatField()


class SpeakingEvaluationSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    overallScore = serializers.FloatField()
    pronunciation = EvaluationScoreSerializer()
    fluency = EvaluationScoreSerializer()
    vocabulary = EvaluationScoreSerializer()
    grammar = EvaluationScoreSerializer()
    coherence = EvaluationScoreSerializer()
    culturalAppropriateness = EvaluationScoreSerializer(required=False, allow_null=True)
    feedback = serializers.CharField()
    suggestions = serializers.ListField(child=serializers.CharField())
    phoneticErrors = PhoneticErrorSerializer(many=True)
    pauses = serializers.ListField(child=serializers.FloatField(), required=False)
    stutters = serializers.IntegerField(required=False)
    createdAt = serializers.CharField()


class SpeakingSessionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk', read_only=True)
    userId = serializers.CharField(source='user_id', read_only=True)
    promptId = serializers.CharField(source='prompt_id', read_only=True)
    audioUrl = serializers.CharField(source='audio_url')
    transcription = serializers.CharField(allow_null=True, required=False)
    evaluation = SpeakingEvaluationSerializer(allow_null=True, required=False)
    duration = serializers.IntegerField()
    createdAt = serializers.DateTimeField(source='created_at')
    status = serializers.CharField()

    class Meta:
        model = PracticeSubmission
        fields = [
            'id', 'userId', 'promptId', 'audioUrl', 'transcription',
            'evaluation', 'duration', 'createdAt', 'status'
        ]
