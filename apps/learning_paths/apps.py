"""
Learning Paths app configuration
"""
from django.apps import AppConfig


class LearningPathsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.learning_paths'
    verbose_name = 'Learning Paths'

    def ready(self):
        """
        Import signal handlers when app is ready
        """
        # Import signals here if needed for learning path events
        # For example: path completion, module unlocking, milestone achievements
        pass
