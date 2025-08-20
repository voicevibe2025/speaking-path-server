"""
URL patterns for Learning Paths
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LearningPathViewSet,
    LearningModuleViewSet,
    ModuleActivityViewSet,
    UserProgressViewSet,
    MilestoneViewSet,
    UserMilestoneViewSet
)

app_name = 'learning_paths'

router = DefaultRouter()
router.register(r'paths', LearningPathViewSet, basename='learning-path')
router.register(r'modules', LearningModuleViewSet, basename='learning-module')
router.register(r'activities', ModuleActivityViewSet, basename='module-activity')
router.register(r'progress', UserProgressViewSet, basename='user-progress')
router.register(r'milestones', MilestoneViewSet, basename='milestone')
router.register(r'achievements', UserMilestoneViewSet, basename='user-milestone')

urlpatterns = [
    path('', include(router.urls)),
]
