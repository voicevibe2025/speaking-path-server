from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class Conversation(models.Model):
    """
    A conversation between two users. Supports one-on-one messaging.
    """
    participant1 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='conversations_as_p1'
    )
    participant2 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='conversations_as_p2'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('participant1', 'participant2')]
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['participant1', 'updated_at']),
            models.Index(fields=['participant2', 'updated_at']),
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        return f"Conversation between {self.participant1_id} and {self.participant2_id}"
    
    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        """Get or create conversation between two users, ensuring canonical ordering."""
        if user1.id > user2.id:
            user1, user2 = user2, user1
        
        conversation, created = cls.objects.get_or_create(
            participant1=user1,
            participant2=user2
        )
        return conversation, created
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation."""
        if self.participant1_id == user.id:
            return self.participant2
        return self.participant1
    
    def has_participant(self, user):
        """Check if user is a participant in this conversation."""
        return self.participant1_id == user.id or self.participant2_id == user.id


class Message(models.Model):
    """
    A message within a conversation.
    """
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    text = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['conversation', 'read_at']),
        ]
    
    def __str__(self):
        return f"Message {self.id} in Conversation {self.conversation_id}"
    
    def mark_as_read(self):
        """Mark this message as read."""
        if not self.read_at:
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
