"""
Users app configuration
"""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Users'

    def ready(self):
        """
        Import signal handlers when app is ready
        """
        # Import signals here if needed
        pass
