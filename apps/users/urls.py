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
    search_users,
    follow_toggle,
    list_followers,
    list_following,
    change_password,
    delete_account,
    PrivacySettingsView,
    block_user,
    list_blocked_users,
    create_report,
    list_my_reports,
    admin_list_reports,
    admin_resolve_report,
)

app_name = 'users'

urlpatterns = [
    # Profile endpoints
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('<int:user_id>/', UserProfileDetailView.as_view(), name='user_profile_detail'),
    path('preferences/', LearningPreferenceView.as_view(), name='preferences'),
    path('change-password/', change_password, name='change_password'),
    path('delete-account/', delete_account, name='delete_account'),

    # Search users
    path('search/', search_users, name='search_users'),

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

    # Privacy Settings
    path('privacy-settings/', PrivacySettingsView.as_view(), name='privacy_settings'),

    # Blocking
    path('block/<int:user_id>/', block_user, name='block_user'),
    path('blocked/', list_blocked_users, name='blocked_users'),

    # Reporting
    path('reports/', create_report, name='create_report'),
    path('reports/my/', list_my_reports, name='my_reports'),
    # Staff moderation
    path('reports/admin/', admin_list_reports, name='admin_list_reports'),
    path('reports/admin/<int:report_id>/resolve/', admin_resolve_report, name='admin_resolve_report'),
]
