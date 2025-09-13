"""
JWT Authentication middleware for Django Channels.
Extracts a JWT from the query string (?token=...) or from the Sec-WebSocket-Protocol header,
validates it using DRF SimpleJWT, and attaches the corresponding user to scope["user"].
"""
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging

logger = logging.getLogger(__name__)


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
                logger.info("WS auth: token found in query param (len=%d)", len(raw))
            else:
                # Optionally look in headers for Authorization: Bearer <token>
                headers = dict(scope.get("headers", []))
                auth_header = headers.get(b"authorization")
                if auth_header:
                    try:
                        val = auth_header.decode()
                        if val.lower().startswith("bearer "):
                            raw = val.split(" ", 1)[1].strip()
                            logger.info("WS auth: token found in Authorization header (len=%d)", len(raw))
                    except Exception:
                        pass

                # Fallback to subprotocol header: Sec-WebSocket-Protocol: "jwt, <token>" or "bearer, <token>"
                if not raw:
                    proto_header = headers.get(b"sec-websocket-protocol")
                    if proto_header:
                        try:
                            parts = [p.strip() for p in proto_header.decode().split(',')]
                            # Expect something like ["jwt", "<token>"] or ["bearer", "<token>"]
                            if len(parts) >= 2 and parts[1]:
                                raw = parts[1]
                                logger.info("WS auth: token found in Sec-WebSocket-Protocol header (len=%d)", len(raw))
                        except Exception:
                            pass

            if raw:
                validated = self.jwt_auth.get_validated_token(raw)
                user = self.jwt_auth.get_user(validated)
                scope_user = user
                logger.info("WS auth: validated user id=%s email=%s", getattr(user, "id", None), getattr(user, "email", None))
            else:
                logger.warning(
                    "WS auth: no token provided. path=%s has_query=%s has_auth_header=%s",
                    scope.get("path"), bool(params), bool(scope.get("headers")) and b"authorization" in dict(scope.get("headers", []))
                )
        except Exception:
            # Keep anonymous on failure; the consumer should close with 4001 if required
            scope_user = AnonymousUser()
            logger.exception("WS auth: exception during JWT validation")

        scope["user"] = scope_user
        return await self.inner(scope, receive, send)
