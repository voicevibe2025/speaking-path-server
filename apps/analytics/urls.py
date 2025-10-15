"""
URL configuration for Analytics app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserAnalyticsViewSet,
    SessionAnalyticsViewSet,
    LearningProgressViewSet,
    ErrorPatternViewSet,
    SkillAssessmentViewSet,
    AnalyticsDashboardViewSet,
    ChatModeUsageViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'user-analytics', UserAnalyticsViewSet, basename='user-analytics')
router.register(r'sessions', SessionAnalyticsViewSet, basename='session-analytics')
router.register(r'progress', LearningProgressViewSet, basename='learning-progress')
router.register(r'error-patterns', ErrorPatternViewSet, basename='error-patterns')
router.register(r'assessments', SkillAssessmentViewSet, basename='skill-assessments')
router.register(r'dashboard', AnalyticsDashboardViewSet, basename='analytics-dashboard')
router.register(r'chat-mode-usage', ChatModeUsageViewSet, basename='chat-mode-usage')

app_name = 'analytics'

urlpatterns = [
    path('', include(router.urls)),
]
