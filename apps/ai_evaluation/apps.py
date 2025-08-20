"""
AI Evaluation app configuration
"""
from django.apps import AppConfig


class AiEvaluationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_evaluation'
    verbose_name = 'AI Evaluation'

    def ready(self):
        """
        Import signal handlers when app is ready
        """
        # Import signals here if needed for AI evaluation events
        pass
