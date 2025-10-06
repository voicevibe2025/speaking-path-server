from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.users.models import PrivacySettings
from .models import Conversation, Message

User = get_user_model()


class MessageParticipantSerializer(serializers.ModelSerializer):
    """Simplified user info for message participants."""
    avatarUrl = serializers.SerializerMethodField()
    displayName = serializers.SerializerMethodField()
    isOnline = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'displayName', 'avatarUrl', 'isOnline']
    
    def get_displayName(self, obj):
        """Get display name with fallbacks."""
        # Try User model's first_name and last_name
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        if obj.first_name:
            return obj.first_name
        # Fallback to username (email)
        return obj.username
    
    def get_avatarUrl(self, obj):
        if hasattr(obj, 'profile') and obj.profile and obj.profile.avatar_url:
            return obj.profile.avatar_url
        return None

    def get_isOnline(self, obj):
        """
        Compute online status from user's last_activity (within 5 minutes).
        Respects the target user's hide_online_status setting.
        Viewer sees their own true status.
        """
        try:
            request = self.context.get('request')
        except Exception:
            request = None

        target_user = obj

        # If viewing own status, always compute true state
        try:
            if request and getattr(request, 'user', None) and request.user.is_authenticated and request.user == target_user:
                if getattr(target_user, 'last_activity', None):
                    threshold = timezone.now() - timedelta(minutes=5)
                    return target_user.last_activity >= threshold
                return False
        except Exception:
            pass

        # Respect privacy settings of target user
        try:
            privacy = PrivacySettings.objects.filter(user=target_user).first()
            if privacy and privacy.hide_online_status:
                return False
        except Exception:
            pass

        # Compute status for other viewers
        try:
            if getattr(target_user, 'last_activity', None):
                threshold = timezone.now() - timedelta(minutes=5)
                return target_user.last_activity >= threshold
        except Exception:
            pass
        return False


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for individual messages."""
    senderId = serializers.IntegerField(source='sender.id', read_only=True)
    senderName = serializers.SerializerMethodField()
    senderAvatar = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    readAt = serializers.DateTimeField(source='read_at', read_only=True)
    isRead = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 
            'text', 
            'senderId', 
            'senderName', 
            'senderAvatar',
            'createdAt', 
            'readAt',
            'isRead'
        ]
    
    def get_senderName(self, obj):
        """Get sender display name with fallbacks."""
        # Try User model's first_name and last_name
        if obj.sender.first_name and obj.sender.last_name:
            return f"{obj.sender.first_name} {obj.sender.last_name}"
        if obj.sender.first_name:
            return obj.sender.first_name
        # Fallback to username (email)
        return obj.sender.username
    
    def get_senderAvatar(self, obj):
        if hasattr(obj.sender, 'profile') and obj.sender.profile and obj.sender.profile.avatar_url:
            return obj.sender.profile.avatar_url
        return None
    
    def get_isRead(self, obj):
        return obj.read_at is not None


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversations with the other participant info."""
    otherUser = serializers.SerializerMethodField()
    lastMessage = serializers.SerializerMethodField()
    unreadCount = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 
            'otherUser', 
            'lastMessage', 
            'unreadCount', 
            'createdAt', 
            'updatedAt'
        ]
    
    def get_otherUser(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        other_user = obj.get_other_participant(request.user)
        return MessageParticipantSerializer(other_user, context={'request': request}).data
    
    def get_lastMessage(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return MessageSerializer(last_message).data
        return None
    
    def get_unreadCount(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        # Count messages not sent by current user that are unread
        return obj.messages.filter(
            read_at__isnull=True
        ).exclude(
            sender=request.user
        ).count()


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a new message."""
    recipientId = serializers.IntegerField()
    text = serializers.CharField(max_length=5000)
    
    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message text cannot be empty.")
        return value.strip()
    
    def validate_recipientId(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient user does not exist.")
        return value


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Detailed conversation serializer with messages."""
    otherUser = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'otherUser', 'messages', 'createdAt', 'updatedAt']
    
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    
    def get_otherUser(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        other_user = obj.get_other_participant(request.user)
        return MessageParticipantSerializer(other_user, context={'request': request}).data
    
    def get_messages(self, obj):
        messages = obj.messages.all().order_by('created_at')
        return MessageSerializer(messages, many=True).data
