"""
Base Django settings for VoiceVibe project.
"""

import os
from pathlib import Path
from datetime import timedelta
import environ

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False)
)

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Read environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'channels',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_extensions',
]

LOCAL_APPS = [
    'apps.authentication',
    'apps.users',
    'apps.learning_paths',
    'apps.speaking_sessions',
    'apps.ai_evaluation',
    'apps.gamification',
    'apps.cultural_adaptation',
    'apps.analytics',
    'apps.speaking_journey',
    'apps.practice',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI and ASGI configuration
WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# Channel layers for WebSocket support
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(env('REDIS_HOST', default='127.0.0.1'), env.int('REDIS_PORT', default=6379))],
        },
    },
}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='voicevibe'),
        'USER': env('DB_USER', default='voicevibe_user'),
        'PASSWORD': env('DB_PASSWORD', default='voicevibe_pass'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Jakarta'  # Indonesian timezone
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'audio_upload': '100/hour',
        'llm_evaluation': '500/day',
    }
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'VoiceVibe',

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "android-app://com.voicevibe",
]

CORS_ALLOW_CREDENTIALS = True

# Email Configuration
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)  # Do not enable together with TLS
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)
EMAIL_TIMEOUT = env.int('EMAIL_TIMEOUT', default=10)

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'VoiceVibe API',
    'DESCRIPTION': 'AI-powered English speaking practice app for Indonesian learners',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Cache Configuration - Using dummy cache for development (no Redis required)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        # 'BACKEND': 'django.core.cache.backends.redis.RedisCache',  # Enable for production
        # 'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        # 'OPTIONS': {},
        # 'KEY_PREFIX': 'voicevibe',
        # 'TIMEOUT': 60 * 15,  # 15 minutes default
    }
}

# Logging: keep dev-server output quiet (only show errors)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    # Default for all loggers
    "root": {
        "handlers": ["console"],
        "level": "ERROR",
    },
    "loggers": {
        # Core Django logs
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        # runserver per-request logs (the noisy ones)
        "django.server": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        # Request/response errors
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        # SQL logs
        "django.db.backends": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        # Local project app logs
        "apps": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# AI API Configuration
AI_CONFIG = {
    'OPENAI_API_KEY': env('OPENAI_API_KEY', default=''),
    'ANTHROPIC_API_KEY': env('ANTHROPIC_API_KEY', default=''),
    'WHISPER_API_KEY': env('WHISPER_API_KEY', default=''),
    'DEFAULT_LLM_MODEL': env('DEFAULT_LLM_MODEL', default='gpt-4'),
    'MAX_TOKENS': env.int('MAX_TOKENS', default=2000),
    'TEMPERATURE': env.float('TEMPERATURE', default=0.7),
}

# Google/Gemini API Keys
GOOGLE_API_KEY = env('GOOGLE_API_KEY', default='')
GEMINI_API_KEY = env('GEMINI_API_KEY', default=GOOGLE_API_KEY)

# Indonesian Cultural Configuration (Hofstede Dimensions)
CULTURAL_CONFIG = {
    'POWER_DISTANCE': 78,
    'INDIVIDUALISM': 14,
    'MASCULINITY': 46,
    'UNCERTAINTY_AVOIDANCE': 48,
    'LONG_TERM_ORIENTATION': 62,
    'INDULGENCE': 38,
}

# Gamification Settings
GAMIFICATION_CONFIG = {
    'ACHIEVEMENT_TYPES': [
        'DAILY_STREAK',
        'WEEKLY_CHALLENGE',
        'GOTONG_ROYONG',  # Collaborative achievement
        'BATIK_PATTERN',  # Cultural badges
        'WAYANG_CHARACTER',  # Character progression
    ],
    'LEADERBOARD_SIZE': 100,
    'STREAK_BONUS_MULTIPLIER': 1.5,
}

# Audio Processing Settings
AUDIO_CONFIG = {
    'MAX_RECORDING_DURATION': 300,  # 5 minutes in seconds
    'SUPPORTED_FORMATS': ['mp3', 'wav', 'webm', 'm4a'],
    'MAX_FILE_SIZE': 50 * 1024 * 1024,  # 50MB
    'SAMPLE_RATE': 16000,
}

# Session Configuration - Using database sessions (more reliable for development)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Store sessions in database
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'  # Enable for production with Redis
# SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week
SESSION_COOKIE_SECURE = False  # Set to True in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
