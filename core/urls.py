"""
VoiceVibe URL Configuration
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# API version prefix
API_V1_PREFIX = 'api/v1/'

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Healthcheck
    path('health/', lambda request: JsonResponse({"status": "ok"})),

    # Friendly index for root path
    path('', lambda request: JsonResponse({
        "name": "VoiceVibe API",
        "version": "v1",
        "docs": request.build_absolute_uri('/api/docs/'),
        "schema": request.build_absolute_uri('/api/schema/'),
        "health": request.build_absolute_uri('/health/'),
        "baseApi": request.build_absolute_uri('/api/v1/')
    })),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1 endpoints
    path(f'{API_V1_PREFIX}auth/', include('apps.authentication.urls')),
    path(f'{API_V1_PREFIX}users/', include('apps.users.urls')),
    path(f'{API_V1_PREFIX}learning/', include('apps.learning_paths.urls')),
    path(f'{API_V1_PREFIX}sessions/', include('apps.speaking_sessions.urls')),
    path(f'{API_V1_PREFIX}evaluate/', include('apps.ai_evaluation.urls')),
    path(f'{API_V1_PREFIX}gamification/', include('apps.gamification.urls')),
    path(f'{API_V1_PREFIX}cultural/', include('apps.cultural_adaptation.urls')),
    path(f'{API_V1_PREFIX}analytics/', include('apps.analytics.urls')),
    path(f'{API_V1_PREFIX}speaking/', include('apps.speaking_journey.urls')),
    path(f'{API_V1_PREFIX}practice/', include('apps.practice.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
else:
    # In production, serve media files (e.g., cached TTS WAVs) directly from Django.
    # Consider moving to a CDN/object storage for scale.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
    ]
