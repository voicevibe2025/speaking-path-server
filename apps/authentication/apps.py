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
        Initialize integrations (e.g., Firebase Admin) on app startup.
        Avoid per-request initialization and hardcoded local paths.
        """
        try:
            from .firebase import init_firebase
            init_ok = init_firebase()
            if not init_ok:
                # Do not crash app; login view will return a helpful error if still uninitialized
                import logging
                logging.getLogger(__name__).warning(
                    "Firebase Admin not initialized at startup (missing env?). Google login may fail until configured."
                )
        except Exception:
            # Never raise at import time; just log
            import logging
            logging.getLogger(__name__).exception("Error during AuthenticationConfig.ready() initialization")
