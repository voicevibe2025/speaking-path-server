from rest_framework import serializers


class ConversationTurnSerializer(serializers.Serializer):
    speaker = serializers.CharField()
    text = serializers.CharField()


class SpeakingTopicDtoSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    material = serializers.ListField(child=serializers.CharField())
    conversation = ConversationTurnSerializer(many=True, required=False)
    unlocked = serializers.BooleanField()
    completed = serializers.BooleanField()


class SpeakingTopicsResponseSerializer(serializers.Serializer):
    topics = SpeakingTopicDtoSerializer(many=True)


class CompleteTopicResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    completedTopicId = serializers.CharField()
    unlockedTopicId = serializers.CharField(allow_null=True)
