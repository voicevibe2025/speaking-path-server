"""
WebSocket consumer for real-time messaging
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message
from .serializers import MessageSerializer

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat in a conversation.
    """
    
    async def connect(self):
        """Accept WebSocket connection and join conversation room."""
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']
        
        # Verify user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Verify user is participant in this conversation
        is_participant = await self.verify_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Leave conversation room."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                # Handle new message
                text = data.get('text', '').strip()
                if not text:
                    return
                
                # Save message to database
                message = await self.save_message(text)
                
                # Serialize message
                message_data = await self.serialize_message(message)
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_data
                    }
                )
            
            elif message_type == 'typing':
                # Handle typing indicator
                is_typing = data.get('isTyping', False)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': self.user.id,
                        'is_typing': is_typing
                    }
                )
            
            elif message_type == 'mark_read':
                # Mark messages as read
                await self.mark_conversation_read()
                
        except json.JSONDecodeError:
            pass
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def chat_message(self, event):
        """Send chat message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'userId': event['user_id'],
                'isTyping': event['is_typing']
            }))
    
    @database_sync_to_async
    def verify_participant(self):
        """Verify user is a participant in the conversation."""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.user1 == self.user or conversation.user2 == self.user
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, text):
        """Save message to database."""
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            text=text
        )
        return message
    
    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message object."""
        serializer = MessageSerializer(message)
        return serializer.data
    
    @database_sync_to_async
    def mark_conversation_read(self):
        """Mark all messages in conversation as read by current user."""
        conversation = Conversation.objects.get(id=self.conversation_id)
        conversation.messages.exclude(sender=self.user).filter(
            read_at__isnull=True
        ).update(read_at=timezone.now())
