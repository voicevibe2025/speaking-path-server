"""
Core middlewares for VoiceVibe
"""
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class MaintenanceModeMiddleware(MiddlewareMixin):
    """Return JSON 503 for API requests when MAINTENANCE_MODE is enabled.

    - Applies to paths under /api/ (including /api/v1/)
    - Skips health endpoints and schema/docs to keep deploy healthchecks working
    - Skips the system status endpoint so it can report details even during maintenance
    """

    def process_request(self, request):
        if not getattr(settings, 'MAINTENANCE_MODE', False):
            return None

        path = request.path or ""
        # Allow health and docs
        allow_paths = (
            '/health/', '/health/db/', '/api/schema/', '/api/docs/', '/api/redoc/',
            '/api/v1/system/status/'
        )
        if any(path.startswith(p) for p in allow_paths):
            return None

        # Only intercept API paths
        if not path.startswith('/api/'):
            return None

        data = {
            'status': 'maintenance',
            'message': getattr(
                settings,
                'MAINTENANCE_MESSAGE',
                'We are performing scheduled maintenance. Please try again later.'
            )
        }
        retry_after = getattr(settings, 'MAINTENANCE_RETRY_AFTER', 0) or None
        resp = JsonResponse(data, status=503)
        if retry_after:
            resp['Retry-After'] = str(int(retry_after))
        return resp
