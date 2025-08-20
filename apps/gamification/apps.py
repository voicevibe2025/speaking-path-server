"""
Django app configuration for Gamification
"""
from django.apps import AppConfig


class GamificationConfig(AppConfig):
    """
    Configuration for the Gamification app with Indonesian cultural elements
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.gamification'
    verbose_name = 'Gamification System'

    def ready(self):
        """
        Initialize app when Django starts
        """
        # Import signal handlers here to avoid circular imports
        try:
            from . import signals
        except ImportError:
            pass
