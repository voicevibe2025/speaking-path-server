"""
Middleware for tracking user activity
"""
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class UpdateLastActivityMiddleware(MiddlewareMixin):
    """
    Middleware to update user's last_activity timestamp on every authenticated request
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            # Update last_activity to now
            # Use update() to avoid triggering save signals and updated_at changes
            request.user.__class__.objects.filter(pk=request.user.pk).update(
                last_activity=timezone.now()
            )
        return None
