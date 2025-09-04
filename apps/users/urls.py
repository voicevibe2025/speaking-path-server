"""
User profile URL patterns for VoiceVibe
"""
from django.urls import path
from .views import (
    UserProfileView,
    UserProfileDetailView,
    LearningPreferenceView,
    UserAchievementListView,
    UserAchievementDetailView,
    UserStatsView,
    update_streak,
    add_practice_time,
)

app_name = 'users'

urlpatterns = [
    # Profile endpoints
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('<int:user_id>/', UserProfileDetailView.as_view(), name='user_profile_detail'),
    path('preferences/', LearningPreferenceView.as_view(), name='preferences'),

    # Achievement endpoints
    path('achievements/', UserAchievementListView.as_view(), name='achievements_list'),
    path('achievements/<int:pk>/', UserAchievementDetailView.as_view(), name='achievement_detail'),

    # Statistics endpoints
    path('stats/', UserStatsView.as_view(), name='stats'),
    path('streak/update/', update_streak, name='update_streak'),
    path('practice-time/add/', add_practice_time, name='add_practice_time'),
]
