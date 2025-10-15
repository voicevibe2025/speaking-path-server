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
# Temporarily using simpler storage to fix admin 500 error
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

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

# Connection persistence (helps reduce reconnect churn)
if "default" in DATABASES:
    DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# Optional: force IPv4 for DB connections when the platform lacks IPv6 egress
# When FORCE_IPV4_DB=true, resolve the DB host to IPv4 and pass it via psycopg2's hostaddr.
# This preserves HOST for clarity while ensuring IPv4 is used.
FORCE_IPV4_DB = env.bool("FORCE_IPV4_DB", default=False)
if FORCE_IPV4_DB and "default" in DATABASES:
    try:
        import socket
        db_host = DATABASES["default"].get("HOST")
        if db_host:
            info = socket.getaddrinfo(db_host, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
            if info:
                ipv4_addr = info[0][4][0]
                DATABASES["default"].setdefault("OPTIONS", {})
                # psycopg2/libpq will honor hostaddr when provided
                DATABASES["default"]["OPTIONS"]["hostaddr"] = ipv4_addr
    except Exception:
        # Do not crash if resolution fails; just skip forcing IPv4
        pass

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

# Media root / storage
# Option A (default): local disk, optionally backed by a Railway Volume via MEDIA_ROOT
# Option B: S3-compatible storage when USE_S3_MEDIA=true
# Option C: Supabase Storage for persistent avatar storage
MEDIA_ROOT = env("MEDIA_ROOT", default=MEDIA_ROOT)
USE_S3_MEDIA = env.bool("USE_S3_MEDIA", default=False)

# Supabase Storage Configuration (using native API, not S3-compatible)
SUPABASE_URL = env("SUPABASE_URL", default="")
SUPABASE_SERVICE_ROLE_KEY = env("SUPABASE_SERVICE_ROLE_KEY", default="")
SUPABASE_STORAGE_BUCKET_NAME = env("SUPABASE_STORAGE_BUCKET_NAME", default="avatars")
SUPABASE_AVATARS_BUCKET_NAME = env("SUPABASE_AVATARS_BUCKET_NAME", default="avatars")

# Check if Supabase Storage is properly configured
SUPABASE_CONFIGURED = bool(
    SUPABASE_URL and 
    SUPABASE_SERVICE_ROLE_KEY
)

if USE_S3_MEDIA:
    # django-storages S3 backend
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default=None)
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)  # e.g., R2/B2 endpoint
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default=None)  # optional CDN/custom domain
    AWS_QUERYSTRING_AUTH = env.bool("AWS_QUERYSTRING_AUTH", default=False)  # public URLs by default

    # Compute MEDIA_URL for public access
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN.rstrip('/')}/"
    elif AWS_S3_ENDPOINT_URL:
        MEDIA_URL = f"{AWS_S3_ENDPOINT_URL.rstrip('/')}/{AWS_STORAGE_BUCKET_NAME}/"
    else:
        MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
else:
    # Ensure media directory exists (helpful when mounting a fresh Railway Volume)
    try:
        os.makedirs(str(MEDIA_ROOT), exist_ok=True)
    except Exception:
        pass

# Log Supabase configuration status for debugging
import logging
logger = logging.getLogger(__name__)
if SUPABASE_CONFIGURED:
    logger.info("Supabase Storage is configured for avatar persistence")
else:
    logger.warning("Supabase Storage not configured - avatars will be stored locally and may be lost on deployment")

# --- Logging ---
LOGGING["root"]["level"] = "INFO"
LOGGING["loggers"]["django"]["level"] = "INFO"
LOGGING["loggers"].setdefault("apps", {"handlers": ["console"], "level": "INFO", "propagate": False})
LOGGING["loggers"]["apps"]["level"] = "INFO"

# --- Sentry (optional) ---
SENTRY_DSN = (env("SENTRY_DSN", default="") or "").strip()
if SENTRY_DSN and "://" in SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=float(env("SENTRY_TRACES_SAMPLE_RATE", default="0.0")),
            send_default_pii=True,
        )
    except Exception:
        # Do not allow Sentry misconfiguration to crash the app
        pass
