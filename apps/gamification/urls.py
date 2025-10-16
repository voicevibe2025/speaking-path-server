"""
URL routing for Gamification app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserLevelViewSet,
    BadgeViewSet,
    UserBadgeViewSet,
    GotongRoyongChallengeViewSet,
    LeaderboardViewSet,
    DailyQuestViewSet,
    RewardShopViewSet,
    UserRewardViewSet,
    AchievementEventViewSet,
)

app_name = 'gamification'

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'user-levels', UserLevelViewSet, basename='userlevel')
router.register(r'badges', BadgeViewSet, basename='badge')
router.register(r'user-badges', UserBadgeViewSet, basename='userbadge')
router.register(r'challenges', GotongRoyongChallengeViewSet, basename='challenge')
router.register(r'leaderboards', LeaderboardViewSet, basename='leaderboard')
router.register(r'daily-quests', DailyQuestViewSet, basename='dailyquest')
router.register(r'reward-shop', RewardShopViewSet, basename='rewardshop')
router.register(r'user-rewards', UserRewardViewSet, basename='userreward')
router.register(r'achievement-events', AchievementEventViewSet, basename='achievementevent')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
