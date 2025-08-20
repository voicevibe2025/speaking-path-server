"""
URL configuration for Cultural Adaptation app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CulturalProfileViewSet,
    CulturalScenarioViewSet,
    CulturalFeedbackTemplateViewSet,
    IndonesianEnglishMappingViewSet,
    CulturalAdaptationPreferenceViewSet
)

app_name = 'cultural_adaptation'

router = DefaultRouter()
router.register(r'profiles', CulturalProfileViewSet, basename='cultural-profile')
router.register(r'scenarios', CulturalScenarioViewSet, basename='cultural-scenario')
router.register(r'feedback-templates', CulturalFeedbackTemplateViewSet, basename='feedback-template')
router.register(r'language-mappings', IndonesianEnglishMappingViewSet, basename='language-mapping')
router.register(r'preferences', CulturalAdaptationPreferenceViewSet, basename='adaptation-preference')

urlpatterns = [
    path('', include(router.urls)),
]
