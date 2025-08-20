"""
WebSocket URL routing for speaking sessions
"""
from django.urls import re_path
from .consumers import AudioStreamConsumer

websocket_urlpatterns = [
    re_path(
        r'ws/audio/session/(?P<session_id>[0-9a-f-]+)/$',
        AudioStreamConsumer.as_asgi()
    ),
]
