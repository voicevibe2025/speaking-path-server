from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Word(models.Model):
    """
    Vocabulary words for the WordUp! feature.
    """
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    word = models.CharField(max_length=100, unique=True, db_index=True)
    definition = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    example_sentence = models.TextField(blank=True, help_text="Optional example sentence")
    part_of_speech = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['word']
        indexes = [
            models.Index(fields=['difficulty']),
        ]
    
    def __str__(self):
        return f"{self.word} ({self.difficulty})"


class UserWordProgress(models.Model):
    """
    Tracks user's progress on individual words.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='word_progress')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='user_progress')
    
    # Progress tracking
    is_mastered = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    user_example_sentence = models.TextField(blank=True)
    
    # Timestamps
    first_attempted_at = models.DateTimeField(auto_now_add=True)
    mastered_at = models.DateTimeField(null=True, blank=True)
    last_practiced_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'word']
        ordering = ['-last_practiced_at']
        indexes = [
            models.Index(fields=['user', 'is_mastered']),
            models.Index(fields=['user', '-last_practiced_at']),
        ]
    
    def __str__(self):
        status = "Mastered" if self.is_mastered else "Learning"
        return f"{self.user.username} - {self.word.word} ({status})"
