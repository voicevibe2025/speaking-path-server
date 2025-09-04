"""
Views for Gamification app with Indonesian cultural elements
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.db import transaction
import logging
from datetime import timedelta

from .models import (
    UserLevel,
    Badge,
    UserBadge,
    GotongRoyongChallenge,
    ChallengeParticipation,
    Leaderboard,
    LeaderboardEntry,
    DailyQuest,
    UserQuest,
    RewardShop,
    UserReward
)
from .serializers import (
    UserLevelSerializer,
    BadgeSerializer,
    UserBadgeSerializer,
    GotongRoyongChallengeSerializer,
    ChallengeParticipationSerializer,
    LeaderboardSerializer,
    LeaderboardEntrySerializer,
    DailyQuestSerializer,
    UserQuestSerializer,
    RewardShopSerializer,
    UserRewardSerializer,
    PurchaseRewardSerializer,
    JoinChallengeSerializer,
    UpdateStreakSerializer
)

logger = logging.getLogger(__name__)


class UserLevelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user level and experience management
    """
    serializer_class = UserLevelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get user level profile"""
        return UserLevel.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's level profile"""
        try:
            profile = UserLevel.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserLevel.DoesNotExist:
            # Create profile if doesn't exist
            profile = UserLevel.objects.create(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def add_experience(self, request):
        """Add experience points to user"""
        points = request.data.get('points', 0)
        source = request.data.get('source', 'unknown')
        
        try:
            profile = UserLevel.objects.get(user=request.user)
            old_level = profile.current_level
            
            # Add points
            profile.experience_points += points
            profile.total_points_earned += points
            
            # Check for level up (100 * level^1.5 points per level)
            while True:
                next_level_points = int(100 * ((profile.current_level + 1) ** 1.5))
                if profile.experience_points >= next_level_points:
                    profile.experience_points -= next_level_points
                    profile.current_level += 1
                    
                    # Update Wayang character based on level
                    if profile.current_level >= 20:
                        profile.wayang_character = 'Yudhistira'
                    elif profile.current_level >= 15:
                        profile.wayang_character = 'Bima'
                    elif profile.current_level >= 10:
                        profile.wayang_character = 'Arjuna'
                    elif profile.current_level >= 7:
                        profile.wayang_character = 'Bagong'
                    elif profile.current_level >= 5:
                        profile.wayang_character = 'Petruk'
                    elif profile.current_level >= 3:
                        profile.wayang_character = 'Gareng'
                else:
                    break
            
            profile.save()
            
            # Check if leveled up
            leveled_up = profile.current_level > old_level
            
            return Response({
                'success': True,
                'points_added': points,
                'current_level': profile.current_level,
                'experience_points': profile.experience_points,
                'wayang_character': profile.wayang_character,
                'leveled_up': leveled_up,
                'new_level': profile.current_level if leveled_up else None
            })
            
        except UserLevel.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def update_streak(self, request):
        """Update user's practice streak"""
        serializer = UpdateStreakSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            profile = UserLevel.objects.get(user=request.user)
            today = timezone.now().date()
            
            # Check if already practiced today
            if profile.last_activity_date == today:
                return Response({
                    'message': 'Already practiced today',
                    'streak_days': profile.streak_days
                })
            
            # Check if streak continues or breaks
            if profile.last_activity_date:
                days_diff = (today - profile.last_activity_date).days
                if days_diff == 1:
                    # Streak continues
                    profile.streak_days += 1
                else:
                    # Streak broken
                    profile.streak_days = 1
            else:
                # First activity
                profile.streak_days = 1
            
            # Update longest streak
            if profile.streak_days > profile.longest_streak:
                profile.longest_streak = profile.streak_days
            
            profile.last_activity_date = today
            profile.save()
            
            # Add bonus points for streak milestones
            bonus_points = 0
            if profile.streak_days in [7, 14, 30, 60, 100]:
                bonus_points = profile.streak_days * 10
                profile.experience_points += bonus_points
                profile.total_points_earned += bonus_points
                profile.save()
            
            return Response({
                'streak_days': profile.streak_days,
                'longest_streak': profile.longest_streak,
                'bonus_points': bonus_points
            })
            
        except UserLevel.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for badges with Batik patterns
    """
    queryset = Badge.objects.filter(is_active=True)
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get badges grouped by category"""
        categories = {}
        for badge in self.get_queryset():
            category = badge.get_category_display()
            if category not in categories:
                categories[category] = []
            categories[category].append(self.get_serializer(badge).data)
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def by_batik_pattern(self, request):
        """Get badges grouped by Batik pattern"""
        patterns = {}
        for badge in self.get_queryset():
            pattern = badge.get_batik_pattern_display()
            if pattern not in patterns:
                patterns[pattern] = []
            patterns[pattern].append(self.get_serializer(badge).data)
        return Response(patterns)


class UserBadgeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user's earned badges
    """
    serializer_class = UserBadgeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get current user's badges"""
        return UserBadge.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def showcase(self, request):
        """Get user's badge showcase (top badges)"""
        badges = self.get_queryset().select_related('badge')[:6]
        serializer = self.get_serializer(badges, many=True)
        return Response(serializer.data)


class GotongRoyongChallengeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Gotong Royong collaborative challenges
    """
    queryset = GotongRoyongChallenge.objects.filter(is_active=True)
    serializer_class = GotongRoyongChallengeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get active challenges"""
        return super().get_queryset().filter(
            end_date__gte=timezone.now()
        )
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a challenge"""
        challenge = self.get_object()
        user = request.user
        
        # Check if already participating
        if ChallengeParticipation.objects.filter(
            challenge=challenge,
            user=user
        ).exists():
            return Response(
                {'error': 'Already participating in this challenge'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if challenge is full
        current_participants = challenge.participants.filter(is_active=True).count()
        if current_participants >= challenge.maximum_participants:
            return Response(
                {'error': 'Challenge is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create participation
        participation = ChallengeParticipation.objects.create(
            challenge=challenge,
            user=user,
            is_active=True
        )
        
        serializer = ChallengeParticipationSerializer(participation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a challenge"""
        challenge = self.get_object()
        user = request.user
        
        try:
            participation = ChallengeParticipation.objects.get(
                challenge=challenge,
                user=user,
                is_active=True
            )
            participation.is_active = False
            participation.save()
            
            return Response({'message': 'Left challenge successfully'})
        except ChallengeParticipation.DoesNotExist:
            return Response(
                {'error': 'Not participating in this challenge'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def contribute(self, request, pk=None):
        """Contribute to challenge progress"""
        challenge = self.get_object()
        user = request.user
        contribution_points = request.data.get('points', 0)
        
        try:
            participation = ChallengeParticipation.objects.get(
                challenge=challenge,
                user=user,
                is_active=True
            )
            
            participation.contribution_score += contribution_points
            
            # Check if challenge goal is met
            total_contributions = challenge.participants.filter(
                is_active=True
            ).aggregate(total=Sum('contribution_score'))['total'] or 0
            
            if total_contributions >= challenge.goal_target:
                # Mark all participants as completed
                challenge.participants.filter(is_active=True).update(
                    completed=True,
                    completed_at=timezone.now()
                )
                
                # Award points to all participants
                for participant in challenge.participants.filter(is_active=True):
                    try:
                        profile = UserLevel.objects.get(user=participant.user)
                        profile.experience_points += challenge.reward_points
                        profile.total_points_earned += challenge.reward_points
                        profile.save()
                    except UserLevel.DoesNotExist:
                        pass
            
            participation.save()
            
            return Response({
                'contribution_added': contribution_points,
                'total_contribution': participation.contribution_score,
                'challenge_progress': total_contributions,
                'challenge_goal': challenge.goal_target
            })
            
        except ChallengeParticipation.DoesNotExist:
            return Response(
                {'error': 'Not participating in this challenge'},
                status=status.HTTP_400_BAD_REQUEST
            )


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for leaderboards
    """
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get weekly leaderboard"""
        period_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
        leaderboard, created = Leaderboard.objects.get_or_create(
            leaderboard_type='weekly',
            period_start=period_start,
            defaults={'period_end': timezone.now()}
        )
        
        # Refresh if older than 1 hour
        if created or (timezone.now() - leaderboard.last_updated).total_seconds() > 3600:
            self._update_leaderboard(leaderboard)
        
        # Return Android-friendly LeaderboardData shape
        data = self._build_leaderboard_response(
            leaderboard=leaderboard,
            request=request,
            type_label='WEEKLY',
            filter_label='WEEKLY_XP'
        )
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Get monthly leaderboard"""
        period_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        leaderboard, created = Leaderboard.objects.get_or_create(
            leaderboard_type='monthly',
            period_start=period_start,
            defaults={'period_end': timezone.now()}
        )
        
        # Refresh if older than 1 hour
        if created or (timezone.now() - leaderboard.last_updated).total_seconds() > 3600:
            self._update_leaderboard(leaderboard)
        
        # Return Android-friendly LeaderboardData shape
        data = self._build_leaderboard_response(
            leaderboard=leaderboard,
            request=request,
            type_label='MONTHLY',
            filter_label='MONTHLY_XP'
        )
        return Response(data)
    
    def _update_leaderboard(self, leaderboard):
        """Update leaderboard entries"""
        # Clear existing entries
        leaderboard.entries.all().delete()
        
        # Get top users by total points
        top_users = UserLevel.objects.all().order_by('-total_points_earned')[:100]
        
        for rank, user_level in enumerate(top_users, 1):
            LeaderboardEntry.objects.create(
                leaderboard=leaderboard,
                user=user_level.user,
                rank=rank,
                score=user_level.total_points_earned,
                wayang_character=user_level.wayang_character
            )
        
        now = timezone.now()
        leaderboard.last_updated = now
        leaderboard.period_end = now
        leaderboard.save()

    def _build_leaderboard_response(self, leaderboard, request, type_label: str, filter_label: str):
        """Construct Android-friendly LeaderboardData payload.
        Matches app's domain model fields and naming.
        """
        entries_qs = leaderboard.entries.select_related('user', 'primary_badge').order_by('rank')

        entries = []
        current_user_entry = None

        for e in entries_qs:
            # Derive user fields
            user = e.user
            try:
                level = user.level_profile.current_level
                streak = user.level_profile.streak_days
            except Exception:
                level = 0
                streak = 0

            display_name = getattr(user, 'get_full_name', None)
            if callable(display_name):
                name_val = (user.get_full_name() or '').strip()
                if not name_val:
                    name_val = user.username
            else:
                name_val = user.username

            badge_obj = None
            if e.primary_badge:
                badge_color = getattr(e.primary_badge, 'pattern_color', None) or '#000000'
                badge_obj = {
                    'id': str(getattr(e.primary_badge, 'badge_id', e.primary_badge.id)),
                    'name': e.primary_badge.name,
                    'icon': e.primary_badge.icon,
                    'color': badge_color,
                }

            entry_data = {
                'rank': e.rank,
                'userId': str(user.id),
                'username': user.username,
                'displayName': name_val,
                'avatarUrl': None,
                'score': e.score,
                'level': level,
                'streakDays': streak,
                'country': None,
                'countryCode': None,
                'isCurrentUser': user.id == getattr(request.user, 'id', None),
                'change': 'NONE',
                'achievements': 0,
                'weeklyXp': e.score if type_label == 'WEEKLY' else 0,
                'monthlyXp': e.score if type_label == 'MONTHLY' else 0,
                'badge': badge_obj,
            }

            if entry_data['isCurrentUser']:
                current_user_entry = entry_data

            entries.append(entry_data)

        data = {
            'type': type_label,
            'filter': filter_label,
            'entries': entries,
            'currentUserEntry': current_user_entry,
            'lastUpdated': leaderboard.last_updated,
            'totalParticipants': len(entries),
        }
        return data


class DailyQuestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for daily quests
    """
    serializer_class = DailyQuestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get today's active quests"""
        today = timezone.now().date()
        return DailyQuest.objects.filter(
            available_date=today,
            is_active=True
        )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a daily quest"""
        quest = self.get_object()
        user = request.user
        
        user_quest, created = UserQuest.objects.get_or_create(
            user=user,
            quest=quest,
            defaults={'current_progress': 0}
        )
        
        serializer = UserQuestSerializer(user_quest)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update quest progress"""
        quest = self.get_object()
        user = request.user
        progress_increment = request.data.get('increment', 1)
        
        try:
            user_quest = UserQuest.objects.get(user=user, quest=quest)
            
            if user_quest.is_completed:
                return Response(
                    {'message': 'Quest already completed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user_quest.current_progress += progress_increment
            
            # Check if quest is completed
            if user_quest.current_progress >= quest.target_value:
                user_quest.is_completed = True
                user_quest.completed_at = timezone.now()
                user_quest.points_earned = quest.experience_points
                
                # Add points to user profile
                try:
                    profile = UserLevel.objects.get(user=user)
                    profile.experience_points += quest.experience_points
                    profile.total_points_earned += quest.experience_points
                    profile.save()
                except UserLevel.DoesNotExist:
                    pass
            
            user_quest.save()
            
            serializer = UserQuestSerializer(user_quest)
            return Response(serializer.data)
            
        except UserQuest.DoesNotExist:
            return Response(
                {'error': 'Quest not started'},
                status=status.HTTP_400_BAD_REQUEST
            )


class RewardShopViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reward shop
    """
    queryset = RewardShop.objects.filter(is_active=True)
    serializer_class = RewardShopSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        """Purchase a reward"""
        reward = self.get_object()
        user = request.user
        
        try:
            profile = UserLevel.objects.get(user=user)
            
            # Check if user can afford
            if profile.total_points_earned < reward.point_cost:
                return Response(
                    {'error': 'Insufficient points'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check level requirement
            if profile.current_level < reward.level_requirement:
                return Response(
                    {'error': f'Requires level {reward.level_requirement}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check stock if limited
            if reward.is_limited:
                if reward.stock_remaining <= 0:
                    return Response(
                        {'error': 'Out of stock'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                reward.stock_remaining -= 1
                reward.save()
            
            # Deduct points and create user reward
            with transaction.atomic():
                profile.total_points_earned -= reward.point_cost
                profile.save()
                
                user_reward = UserReward.objects.create(
                    user=user,
                    reward=reward,
                    acquisition_type='purchase'
                )
            
            serializer = UserRewardSerializer(user_reward)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except UserLevel.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserRewardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user's rewards
    """
    serializer_class = UserRewardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get current user's rewards"""
        return UserReward.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def equip(self, request, pk=None):
        """Equip a reward"""
        user_reward = self.get_object()
        
        # Unequip other rewards of same type
        UserReward.objects.filter(
            user=request.user,
            reward__reward_type=user_reward.reward.reward_type,
            is_active=True
        ).update(is_active=False, equipped_at=None)
        
        # Equip this reward
        user_reward.is_active = True
        user_reward.equipped_at = timezone.now()
        user_reward.save()
        
        serializer = self.get_serializer(user_reward)
        return Response(serializer.data)
