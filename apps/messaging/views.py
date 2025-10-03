from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Max, Count, Case, When, IntegerField
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationDetailSerializer,
    MessageSerializer,
    SendMessageSerializer
)

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    """
    Get all conversations for the current user.
    Returns list of conversations ordered by most recent activity.
    """
    user = request.user
    
    # Get conversations where user is either participant
    conversations = Conversation.objects.filter(
        Q(participant1=user) | Q(participant2=user)
    ).prefetch_related(
        'messages',
        'participant1__profile',
        'participant2__profile'
    ).distinct()
    
    serializer = ConversationSerializer(
        conversations,
        many=True,
        context={'request': request}
    )
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_detail(request, conversation_id):
    """
    Get detailed conversation with all messages.
    Also marks all unread messages as read.
    """
    user = request.user
    
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Verify user is a participant
    if not conversation.has_participant(user):
        return Response(
            {'detail': 'You are not a participant in this conversation.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Mark all unread messages from other user as read
    Message.objects.filter(
        conversation=conversation,
        read_at__isnull=True
    ).exclude(sender=user).update(read_at=timezone.now())
    
    serializer = ConversationDetailSerializer(
        conversation,
        context={'request': request}
    )
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    Send a message to another user.
    Creates conversation if it doesn't exist.
    """
    serializer = SendMessageSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    recipient_id = serializer.validated_data['recipientId']
    text = serializer.validated_data['text']
    
    # Prevent sending message to self
    if recipient_id == request.user.id:
        return Response(
            {'detail': 'Cannot send message to yourself.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Get or create conversation
    conversation, created = Conversation.get_or_create_conversation(
        request.user,
        recipient
    )
    
    # Create message
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        text=text
    )
    
    # Update conversation timestamp
    conversation.save()  # This triggers auto_now on updated_at
    
    return Response(
        MessageSerializer(message).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_or_create_conversation_with_user(request, user_id):
    """
    Get or create a conversation with a specific user.
    Useful for starting a new conversation from user profile.
    """
    if user_id == request.user.id:
        return Response(
            {'detail': 'Cannot create conversation with yourself.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    other_user = get_object_or_404(User, id=user_id)
    
    conversation, created = Conversation.get_or_create_conversation(
        request.user,
        other_user
    )
    
    serializer = ConversationDetailSerializer(
        conversation,
        context={'request': request}
    )
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_messages_count(request):
    """
    Get total count of unread messages for current user.
    """
    user = request.user
    
    # Count all unread messages not sent by current user
    unread_count = Message.objects.filter(
        conversation__participant1=user
    ).exclude(
        sender=user
    ).filter(
        read_at__isnull=True
    ).count() + Message.objects.filter(
        conversation__participant2=user
    ).exclude(
        sender=user
    ).filter(
        read_at__isnull=True
    ).count()
    
    return Response({'unreadCount': unread_count}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_conversation_as_read(request, conversation_id):
    """
    Mark all messages in a conversation as read.
    """
    user = request.user
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Verify user is a participant
    if not conversation.has_participant(user):
        return Response(
            {'detail': 'You are not a participant in this conversation.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Mark all unread messages from other user as read
    updated = Message.objects.filter(
        conversation=conversation,
        read_at__isnull=True
    ).exclude(sender=user).update(read_at=timezone.now())
    
    return Response(
        {'markedAsRead': updated},
        status=status.HTTP_200_OK
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """
    Delete a conversation (and all its messages).
    """
    user = request.user
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Verify user is a participant
    if not conversation.has_participant(user):
        return Response(
            {'detail': 'You are not a participant in this conversation.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    conversation.delete()
    
    return Response(status=status.HTTP_204_NO_CONTENT)
