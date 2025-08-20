"""
VoiceVibe URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# API version prefix
API_V1_PREFIX = 'api/v1/'

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

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
