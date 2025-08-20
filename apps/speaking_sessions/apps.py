"""
Speaking sessions app configuration
"""
from django.apps import AppConfig


class SpeakingSessionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.speaking_sessions'
    verbose_name = 'Speaking Sessions'

    def ready(self):
        """
        Import signal handlers when app is ready
        """
        # Import signals here if needed for session lifecycle events
        pass
