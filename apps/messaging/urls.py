from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Get all conversations
    path('conversations/', views.get_conversations, name='conversations'),
    
    # Get specific conversation with messages
    path('conversations/<int:conversation_id>/', views.get_conversation_detail, name='conversation-detail'),
    
    # Get or create conversation with user
    path('conversations/with-user/<int:user_id>/', views.get_or_create_conversation_with_user, name='conversation-with-user'),
    
    # Send a message
    path('messages/send/', views.send_message, name='send-message'),
    
    # Get unread count
    path('messages/unread-count/', views.get_unread_messages_count, name='unread-count'),
    
    # Mark conversation as read
    path('conversations/<int:conversation_id>/mark-read/', views.mark_conversation_as_read, name='mark-conversation-read'),
    
    # Delete conversation
    path('conversations/<int:conversation_id>/delete/', views.delete_conversation, name='delete-conversation'),
]
