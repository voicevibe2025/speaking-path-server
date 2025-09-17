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
    follow_toggle,
    list_followers,
    list_following,
)

app_name = 'users'

urlpatterns = [
    # Profile endpoints
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('<int:user_id>/', UserProfileDetailView.as_view(), name='user_profile_detail'),
    path('preferences/', LearningPreferenceView.as_view(), name='preferences'),

    # Social: follow/unfollow and lists
    path('follow/<int:user_id>/', follow_toggle, name='follow_toggle'),
    path('followers/', list_followers, name='followers_list_current'),
    path('followers/<int:user_id>/', list_followers, name='followers_list'),
    path('following/', list_following, name='following_list_current'),
    path('following/<int:user_id>/', list_following, name='following_list'),

    # Achievement endpoints
    path('achievements/', UserAchievementListView.as_view(), name='achievements_list'),
    path('achievements/<int:pk>/', UserAchievementDetailView.as_view(), name='achievement_detail'),

    # Statistics endpoints
    path('stats/', UserStatsView.as_view(), name='stats'),
    path('streak/update/', update_streak, name='update_streak'),
    path('practice-time/add/', add_practice_time, name='add_practice_time'),
]
