"""
Authentication models for VoiceVibe
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model for VoiceVibe
    """
    email = models.EmailField(_('email address'), unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last time user made an authenticated request')
    )

    # Override username to use email as primary identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.email


class RefreshTokenBlacklist(models.Model):
    """
    Model to store blacklisted refresh tokens
    """
    token = models.CharField(max_length=500, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blacklisted_tokens')
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'refresh_token_blacklist'
        verbose_name = _('Blacklisted Token')
        verbose_name_plural = _('Blacklisted Tokens')

    def __str__(self):
        return f"Token for {self.user.email} blacklisted at {self.blacklisted_at}"
