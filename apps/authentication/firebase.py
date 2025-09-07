"""
Centralized Firebase Admin initialization for Django.
Supports multiple env sources so it works both locally and on hosted platforms
without relying on absolute file paths.

Environment variables supported:
- FIREBASE_CREDENTIALS_B64: base64-encoded service account JSON
- FIREBASE_CREDENTIALS_JSON: raw service account JSON string
- GOOGLE_APPLICATION_CREDENTIALS: filesystem path to service account JSON (optional)
- FIREBASE_PROJECT_ID or GOOGLE_CLOUD_PROJECT or GCLOUD_PROJECT: project id
"""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Optional

import firebase_admin
from firebase_admin import credentials as fb_credentials

logger = logging.getLogger(__name__)


def _load_credentials_from_env() -> Optional[fb_credentials.Certificate]:
    # Prefer B64 to avoid JSON formatting issues in .env/UIs
    b64 = os.environ.get("FIREBASE_CREDENTIALS_B64")
    print(f"🔍 FIREBASE_CREDENTIALS_B64 present: {bool(b64)}")
    if b64:
        try:
            raw = base64.b64decode(b64)
            data = json.loads(raw)
            print("🔑 Loaded Firebase credentials from FIREBASE_CREDENTIALS_B64")
            logger.info("Loaded Firebase credentials from FIREBASE_CREDENTIALS_B64")
            return fb_credentials.Certificate(data)
        except Exception as e:
            print(f"❌ Failed to parse FIREBASE_CREDENTIALS_B64: {e}")
            logger.exception("Failed to parse FIREBASE_CREDENTIALS_B64: %s", e)

    # Raw JSON string
    raw_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if raw_json:
        try:
            data = json.loads(raw_json)
            logger.info("Loaded Firebase credentials from FIREBASE_CREDENTIALS_JSON")
            return fb_credentials.Certificate(data)
        except Exception as e:
            logger.exception("Failed to parse FIREBASE_CREDENTIALS_JSON: %s", e)

    # Path fallback (optional) - only if it's a valid file path, not base64
    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if sa_path and not sa_path.startswith("ey") and os.path.exists(sa_path):
        try:
            logger.info("Loaded Firebase credentials from file: %s", sa_path)
            return fb_credentials.Certificate(sa_path)
        except Exception as e:
            logger.exception("Failed to load GOOGLE_APPLICATION_CREDENTIALS from path %s: %s", sa_path, e)

    logger.info("No Firebase service account credentials found in env")
    return None


def _get_project_id() -> Optional[str]:
    return (
        os.environ.get("FIREBASE_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCLOUD_PROJECT")
    )


def init_firebase() -> bool:
    """Initialize Firebase Admin if not already initialized.

    Returns True if initialized or already initialized; False if initialization failed.
    """
    try:
        firebase_admin.get_app()
        return True
    except ValueError:
        pass

    # Clear GOOGLE_APPLICATION_CREDENTIALS to prevent auto-loading conflicts
    # We want to use our custom credential loading from FIREBASE_CREDENTIALS_B64
    old_gac = os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    
    try:
        cred = _load_credentials_from_env()
        project_id = _get_project_id()
        options = {"projectId": project_id} if project_id else None

        firebase_admin.initialize_app(cred, options)
        print(f"✅ Firebase Admin initialized (projectId={project_id}, cred={'provided' if cred else 'none'})")
        logger.info(
            "Initialized Firebase Admin (projectId=%s, cred=%s)",
            project_id,
            "provided" if cred else "none",
        )
        return True
    except Exception:
        logger.exception("Firebase Admin init failed")
        return False
    finally:
        # Restore GOOGLE_APPLICATION_CREDENTIALS if it was set
        if old_gac:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = old_gac
