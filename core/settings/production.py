"""
Production settings for VoiceVibe project (Railway-ready).
"""

from .base import *  # noqa

# --- Core ---
DEBUG = env.bool("DEBUG", default=False)

# Allow Railway domains and any additional hosts from env
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[".up.railway.app", ".railway.app", "localhost", "127.0.0.1"],
)

# Trust Railway HTTPS proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
USE_X_FORWARDED_HOST = True

# CSRF
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://*.up.railway.app",
        "https://*.railway.app",
    ],
)

# Static files (served by WhiteNoise)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Database ---
# Prefer a single DATABASE_URL if provided (Railway Postgres) and require SSL
# Guard against an empty string value (which can cause invalid engine warnings)
_db_url_raw = env("DATABASE_URL", default="").strip()
if _db_url_raw:
    _db_url = env.db("DATABASE_URL")
    DATABASES = {"default": _db_url}
    if DATABASES["default"].get("ENGINE", "").startswith("django.db.backends.postgresql"):
        DATABASES["default"].setdefault("OPTIONS", {})
        DATABASES["default"]["OPTIONS"].setdefault("sslmode", "require")
# else fall back to base.py DB_* variables

# --- CORS ---
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=False)
if not CORS_ALLOW_ALL_ORIGINS:
    # Exact origins (comma-separated list in env)
    CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
    # Regex allowance for Railway preview domains
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^https://.*\.up\.railway\.app$",
        r"^https://.*\.railway\.app$",
    ] + env.list("CORS_ALLOWED_ORIGIN_REGEXES", default=[])

# --- Channels / Redis ---
# If REDIS_URL is provided (e.g., Railway Redis), use it for channel layer
_redis_url = env("REDIS_URL", default=None)
if _redis_url:
    CHANNEL_LAYERS["default"] = {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [_redis_url],
        },
    }
else:
    # Safe fallback when Redis is not provisioned
    CHANNEL_LAYERS["default"] = {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }

# Media root (override via env if using a Railway Volume)
MEDIA_ROOT = env("MEDIA_ROOT", default=MEDIA_ROOT)

# --- Logging ---
LOGGING["root"]["level"] = "INFO"
LOGGING["loggers"]["django"]["level"] = "INFO"
LOGGING["loggers"].setdefault("apps", {"handlers": ["console"], "level": "INFO", "propagate": False})
LOGGING["loggers"]["apps"]["level"] = "INFO"

# --- Sentry (optional) ---
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(env("SENTRY_TRACES_SAMPLE_RATE", default="0.0")),
        send_default_pii=True,
    )
