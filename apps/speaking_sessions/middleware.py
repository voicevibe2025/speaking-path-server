"""
JWT Authentication middleware for Django Channels.
Extracts a JWT from the query string (?token=...) or from the Sec-WebSocket-Protocol header,
validates it using DRF SimpleJWT, and attaches the corresponding user to scope["user"].
"""
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


class JwtAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner
        self.jwt_auth = JWTAuthentication()

    async def __call__(self, scope, receive, send):
        # Default to anonymous
        scope_user = AnonymousUser()

        try:
            query_string = scope.get("query_string", b"")
            params = parse_qs(query_string.decode()) if query_string else {}
            raw = None

            # ?token=... takes precedence
            token_list = params.get("token")
            if token_list and len(token_list) > 0:
                raw = token_list[0]
            else:
                # Optionally look in headers for Authorization: Bearer <token>
                headers = dict(scope.get("headers", []))
                auth_header = headers.get(b"authorization")
                if auth_header:
                    try:
                        val = auth_header.decode()
                        if val.lower().startswith("bearer "):
                            raw = val.split(" ", 1)[1].strip()
                    except Exception:
                        pass

            if raw:
                validated = self.jwt_auth.get_validated_token(raw)
                user = self.jwt_auth.get_user(validated)
                scope_user = user
        except Exception:
            # Keep anonymous on failure; the consumer should close with 4001 if required
            scope_user = AnonymousUser()

        scope["user"] = scope_user
        return await self.inner(scope, receive, send)
