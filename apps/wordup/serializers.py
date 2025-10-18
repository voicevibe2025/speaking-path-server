from rest_framework import serializers
from .models import Word, UserWordProgress


class WordSerializer(serializers.ModelSerializer):
    """Serializer for Word model."""
    
    class Meta:
        model = Word
        fields = [
            'id',
            'word',
            'definition',
            'difficulty',
            'example_sentence',
            'part_of_speech',
            'ipa_pronunciation',
        ]


class UserWordProgressSerializer(serializers.ModelSerializer):
    """Serializer for UserWordProgress model."""
    word = WordSerializer(read_only=True)
    word_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = UserWordProgress
        fields = [
            'id',
            'word',
            'word_id',
            'is_mastered',
            'attempts',
            'user_example_sentence',
            'first_attempted_at',
            'mastered_at',
            'last_practiced_at',
        ]
        read_only_fields = ['first_attempted_at', 'last_practiced_at']


class EvaluateExampleRequest(serializers.Serializer):
    """Request serializer for evaluating example sentences."""
    word_id = serializers.IntegerField()
    example_sentence = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    audio_base64 = serializers.CharField(required=False, allow_blank=True)


class EvaluateExampleResponse(serializers.Serializer):
    """Response serializer for example sentence evaluation."""
    is_acceptable = serializers.BooleanField()
    feedback = serializers.CharField()
    word_id = serializers.IntegerField()
    is_mastered = serializers.BooleanField()


class MasterWordRequest(serializers.Serializer):
    """Request serializer for mastering a word."""
    word_id = serializers.IntegerField()
    example_sentence = serializers.CharField(max_length=500)


class EvaluatePronunciationRequest(serializers.Serializer):
    """Request serializer for evaluating pronunciation."""
    word_id = serializers.IntegerField()
    audio_base64 = serializers.CharField(required=True)


class EvaluatePronunciationResponse(serializers.Serializer):
    """Response serializer for pronunciation evaluation."""
    is_correct = serializers.BooleanField()
    transcribed_text = serializers.CharField()
    feedback = serializers.CharField()
    confidence = serializers.FloatField()
