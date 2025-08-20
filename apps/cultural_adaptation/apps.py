"""
App configuration for Cultural Adaptation
"""
from django.apps import AppConfig


class CulturalAdaptationConfig(AppConfig):
    """
    Configuration for Cultural Adaptation app
    Handles Indonesian cultural context and personalization
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cultural_adaptation'
    verbose_name = 'Cultural Adaptation'

    def ready(self):
        """
        Import signals and perform app initialization
        """
        # Import signals when app is ready
        # from . import signals
        pass
