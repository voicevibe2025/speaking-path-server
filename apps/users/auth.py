from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication


class ActiveUserJWTAuthentication(JWTAuthentication):
    """
    JWT authentication that also updates user's last_activity timestamp
    on successful authentication.
    This ensures online status works for token-authenticated API requests.
    """
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        # Update last_activity without triggering signals
        User = get_user_model()
        try:
            User.objects.filter(pk=user.pk).update(last_activity=timezone.now())
        except Exception:
            # Avoid breaking auth if DB update fails
            pass
        return user
