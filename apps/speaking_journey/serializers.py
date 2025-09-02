from rest_framework import serializers


class ConversationTurnSerializer(serializers.Serializer):
    speaker = serializers.CharField()
    text = serializers.CharField()


class PhraseProgressSerializer(serializers.Serializer):
    currentPhraseIndex = serializers.IntegerField()
    completedPhrases = serializers.ListField(child=serializers.IntegerField())
    totalPhrases = serializers.IntegerField()
    isAllPhrasesCompleted = serializers.BooleanField()


class SpeakingTopicDtoSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    material = serializers.ListField(child=serializers.CharField())
    conversation = ConversationTurnSerializer(many=True, required=False)
    phraseProgress = PhraseProgressSerializer(required=False)
    unlocked = serializers.BooleanField()
    completed = serializers.BooleanField()


class UserProfileSerializer(serializers.Serializer):
    firstVisit = serializers.BooleanField()
    lastVisitedTopicId = serializers.CharField(allow_null=True, required=False)
    lastVisitedTopicTitle = serializers.CharField(allow_blank=True, required=False)


class SpeakingTopicsResponseSerializer(serializers.Serializer):
    topics = SpeakingTopicDtoSerializer(many=True)
    userProfile = UserProfileSerializer()


class CompleteTopicResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    completedTopicId = serializers.CharField()
    unlockedTopicId = serializers.CharField(allow_null=True)


class PhraseSubmissionResultSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    accuracy = serializers.FloatField()
    transcription = serializers.CharField()
    feedback = serializers.CharField(allow_blank=True, required=False)
    nextPhraseIndex = serializers.IntegerField(allow_null=True, required=False)
    topicCompleted = serializers.BooleanField(default=False)
    xpAwarded = serializers.IntegerField(default=0)
    recordingId = serializers.CharField(allow_null=True, required=False)
    audioUrl = serializers.CharField(allow_blank=True, required=False)


class UserPhraseRecordingSerializer(serializers.Serializer):
    id = serializers.CharField()
    phraseIndex = serializers.IntegerField(source='phrase_index')
    audioUrl = serializers.SerializerMethodField()
    transcription = serializers.CharField(allow_blank=True)
    accuracy = serializers.FloatField(allow_null=True)
    feedback = serializers.CharField(allow_blank=True)
    createdAt = serializers.DateTimeField(source='created_at')

    def get_audioUrl(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        try:
            url = obj.audio_file.url if obj.audio_file else ''
        except Exception:
            url = ''
        if request and url:
            return request.build_absolute_uri(url)
        return url


class UserPhraseRecordingsResponseSerializer(serializers.Serializer):
    recordings = UserPhraseRecordingSerializer(many=True)
