"""
Core views for system-level endpoints
"""
from django.conf import settings
from django.http import JsonResponse


def system_status_view(request):
    """Return current system status and maintenance info.

    If MAINTENANCE_MODE is on, respond 503 and include message and retry-after seconds.
    Otherwise respond 200 with status ok.
    """
    maintenance = getattr(settings, 'MAINTENANCE_MODE', False)
    message = getattr(settings, 'MAINTENANCE_MESSAGE', '')
    retry_after = getattr(settings, 'MAINTENANCE_RETRY_AFTER', 0) or None

    data = {
        "status": "maintenance" if maintenance else "ok",
        "maintenance": bool(maintenance),
        "message": message,
        "retryAfterSeconds": retry_after,
    }
    status_code = 503 if maintenance else 200
    resp = JsonResponse(data, status=status_code)
    if maintenance and retry_after:
        resp['Retry-After'] = str(int(retry_after))
    return resp
