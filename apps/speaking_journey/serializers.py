from rest_framework import serializers


class SpeakingTopicDtoSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    material = serializers.ListField(child=serializers.CharField())
    unlocked = serializers.BooleanField()
    completed = serializers.BooleanField()


class SpeakingTopicsResponseSerializer(serializers.Serializer):
    topics = SpeakingTopicDtoSerializer(many=True)


class CompleteTopicResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    completedTopicId = serializers.CharField()
    unlockedTopicId = serializers.CharField(allow_null=True)
