"""
Authentication app configuration
"""
from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    verbose_name = 'Authentication'

    def ready(self):
        """
        Import signal handlers when app is ready
        """
        pass  # Add signal imports here if needed
