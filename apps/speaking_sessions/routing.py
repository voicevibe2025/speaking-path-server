"""
WebSocket URL routing for speaking sessions
"""
from django.urls import re_path
from .consumers import AudioStreamConsumer, GeminiLiveProxyConsumer

websocket_urlpatterns = [
    re_path(
        r'ws/audio/session/(?P<session_id>[0-9a-f-]+)/$',
        AudioStreamConsumer.as_asgi()
    ),
    re_path(
        r'ws/live/session/(?P<session_id>[0-9a-f-]+)/$',
        GeminiLiveProxyConsumer.as_asgi()
    ),
]
