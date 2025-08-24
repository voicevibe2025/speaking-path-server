"""
Development settings for VoiceVibe project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']  # Allow all hosts in development (covers 192.168.18.136, emulator, localhost)

# Database - Use Supabase PostgreSQL for development
# DATABASES configuration is inherited from base.py (Supabase)
# If you want to use SQLite for development, uncomment the lines below:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Email Backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable some security in development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Media files
MEDIA_ROOT = BASE_DIR / 'media_dev'

# Simplified logging for development
LOGGING['loggers']['django']['level'] = 'ERROR'
# Ensure 'apps' logger exists and keep it quiet by default
LOGGING['loggers'].setdefault('apps', {
    'handlers': ['console'],
    'level': 'ERROR',
    'propagate': False,
})
LOGGING['loggers']['apps']['level'] = 'ERROR'

# Celery - Use synchronous mode in development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# AI API Configuration - Development
AI_CONFIG.update({
    'USE_MOCK_RESPONSES': env.bool('USE_MOCK_AI', default=True),  # Use mock responses to save API costs
    'MOCK_DELAY': 1.0,  # Simulate API delay
})
