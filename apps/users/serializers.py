"""
User profile serializers for VoiceVibe
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange

from apps.authentication.models import User
from .models import UserProfile, LearningPreference, UserAchievement, UserFollow
from apps.gamification.serializers import UserBadgeSerializer
from apps.speaking_sessions.models import PracticeSession
from apps.learning_paths.models import UserProgress
from apps.speaking_journey.models import TopicProgress, UserPhraseRecording, VocabularyPracticeSession

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    displayName = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', allow_blank=True, required=False)

    # New avatar fields
    avatar = serializers.ImageField(write_only=True, required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField()

    # Required fields to match frontend UserProfile data class
    level = serializers.IntegerField(source='user.level_profile.current_level', default=1)
    xp = serializers.IntegerField(source='user.level_profile.experience_points', default=0)
    xpToNextLevel = serializers.SerializerMethodField()
    streakDays = serializers.IntegerField(source='user.level_profile.streak_days', default=0)
    longestStreak = serializers.SerializerMethodField()
    joinedDate = serializers.DateTimeField(source='user.date_joined', read_only=True)
    lastActiveDate = serializers.DateTimeField(source='user.last_login', read_only=True)
    language = serializers.CharField(source='target_language', default='English')
    isVerified = serializers.BooleanField(default=False)
    isPremium = serializers.BooleanField(default=False)
    isOnline = serializers.BooleanField(default=False)
    isFollowing = serializers.SerializerMethodField()
    isFollower = serializers.SerializerMethodField()
    isBlocked = serializers.BooleanField(default=False)
    followersCount = serializers.SerializerMethodField()
    followingCount = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    preferences = serializers.SerializerMethodField()
    # Computed proficiency based on Speaking Journey topics mastered
    current_proficiency = serializers.SerializerMethodField()
    
    # Legacy fields for backward compatibility
    current_level = serializers.IntegerField(source='user.level_profile.current_level', read_only=True)
    experience_points = serializers.IntegerField(source='user.level_profile.experience_points', read_only=True)
    total_points_earned = serializers.IntegerField(source='user.level_profile.total_points_earned', read_only=True, default=0)
    streak_days = serializers.IntegerField(source='user.level_profile.streak_days', read_only=True)

    # Quick Stats now computed from Speaking Journey data
    total_practice_hours = serializers.SerializerMethodField()
    lessons_completed = serializers.SerializerMethodField()
    recordings_count = serializers.SerializerMethodField()
    avg_score = serializers.SerializerMethodField()

    # Recent Achievements from UserBadge model
    recent_achievements = serializers.SerializerMethodField()

    # Learning Preferences from UserProfile model
    daily_practice_goal = serializers.IntegerField(read_only=True)
    learning_goal = serializers.CharField(read_only=True)
    target_language = serializers.CharField(read_only=True)

    # Skill Progress computed from Speaking Journey models (not analytics)
    speaking_score = serializers.SerializerMethodField()
    listening_score = serializers.SerializerMethodField()
    grammar_score = serializers.SerializerMethodField()
    vocabulary_score = serializers.SerializerMethodField()
    pronunciation_score = serializers.SerializerMethodField()

    # Monthly Progress
    monthly_days_active = serializers.SerializerMethodField()
    monthly_xp_earned = serializers.SerializerMethodField()
    monthly_lessons_completed = serializers.SerializerMethodField()

    # Recent Activities Feed
    recent_activities = serializers.SerializerMethodField()

    # Membership Status
    membership_status = serializers.SerializerMethodField()

    def get_total_practice_hours(self, obj):
        """
        Speaking Journey practice hours (approx):
        - Sum durations of VocabularyPracticeSession (updated_at - created_at)
        - Estimate Pronunciation time from count of UserPhraseRecording (avg 12s each)
        - Estimate Fluency time from number of recorded prompt scores (avg 60s each)

        Returns hours rounded to 1 decimal place.
        """
        user = obj.user
        # 1) Vocabulary sessions duration
        vocab_qs = VocabularyPracticeSession.objects.filter(user=user)
        vocab_seconds = 0.0
        for s in vocab_qs.only('created_at', 'updated_at'):
            try:
                if s.created_at and s.updated_at:
                    delta = (s.updated_at - s.created_at).total_seconds()
                    # Guard against negative or extreme values
                    if 0 <= delta < 3 * 3600:
                        vocab_seconds += delta
            except Exception:
                continue

        # 2) Pronunciation recordings estimate
        recordings_count = UserPhraseRecording.objects.filter(user=user).count()
        AVG_SEC_PER_RECORDING = 12  # heuristic
        pron_seconds = recordings_count * AVG_SEC_PER_RECORDING

        # 3) Fluency prompts estimate
        fluency_prompts_done = 0
        for row in TopicProgress.objects.filter(user=user).values_list('fluency_prompt_scores', flat=True):
            try:
                arr = list(row or [])
            except Exception:
                arr = []
            fluency_prompts_done += sum(1 for v in arr if isinstance(v, int))
        AVG_SEC_PER_FLUENCY_PROMPT = 60  # heuristic
        fluency_seconds = fluency_prompts_done * AVG_SEC_PER_FLUENCY_PROMPT

        total_seconds = float(vocab_seconds) + float(pron_seconds) + float(fluency_seconds)
        hours = round(total_seconds / 3600.0, 1)
        return max(0.0, hours)

    def get_lessons_completed(self, obj):
        """Number of Speaking Journey topics completed."""
        return TopicProgress.objects.filter(user=obj.user, completed=True).count()

    def get_current_proficiency(self, obj):
        """
        Map number of mastered Speaking Journey topics to a named proficiency tier.

        Tiers:
        0–10   -> Chaucerite 🌱
        11–20  -> Shakespire 🎭
        21–30  -> Miltonarch 🔥
        31–40  -> Austennova 💫
        41–50  -> Dickenlord 📚
        51–60  -> Joycemancer 🌀
        61+    -> The Bard Eternal 👑
        """
        try:
            topics_mastered = int(self.get_lessons_completed(obj))
        except Exception:
            topics_mastered = 0

        if topics_mastered <= 10:
            return "Chaucerite 🌱"
        elif topics_mastered <= 20:
            return "Shakespire 🎭"
        elif topics_mastered <= 30:
            return "Miltonarch 🔥"
        elif topics_mastered <= 40:
            return "Austennova 💫"
        elif topics_mastered <= 50:
            return "Dickenlord 📚"
        elif topics_mastered <= 60:
            return "Joycemancer 🌀"
        else:
            return "The Bard Eternal 👑"

    def get_recordings_count(self, obj):
        """Total pronunciation recordings submitted in Speaking Journey."""
        return UserPhraseRecording.objects.filter(user=obj.user).count()

    def get_avg_score(self, obj):
        """
        Average score across Speaking Journey modes (0-100):
        - Pronunciation: average of recording accuracies
        - Fluency: average of all prompt scores across topics
        - Vocabulary: average percent across completed sessions
        Overall average is the mean of available mode averages.
        """
        user = obj.user
        mode_avgs = []

        # Pronunciation average (accuracy)
        try:
            pron_avg = UserPhraseRecording.objects.filter(user=user, accuracy__isnull=False).aggregate(avg=Avg('accuracy'))['avg'] or 0.0
            if pron_avg > 0:
                mode_avgs.append(float(pron_avg))
        except Exception:
            pass

        # Fluency average (prompt scores)
        try:
            scores = []
            for row in TopicProgress.objects.filter(user=user).values_list('fluency_prompt_scores', flat=True):
                try:
                    arr = list(row or [])
                except Exception:
                    arr = []
                for v in arr:
                    if isinstance(v, int):
                        scores.append(int(v))
            if scores:
                mode_avgs.append(sum(scores) / len(scores))
        except Exception:
            pass

        # Vocabulary average (completed sessions normalized to 0-100)
        try:
            v_sessions = VocabularyPracticeSession.objects.filter(user=user, completed=True)
            percents = []
            for s in v_sessions.only('total_questions', 'total_score'):
                tq = int(s.total_questions or 0)
                ts = int(s.total_score or 0)
                if tq > 0:
                    max_score = tq * 10
                    perc = max(0.0, min(100.0, (ts / max(max_score, 1)) * 100.0))
                    percents.append(perc)
            if percents:
                mode_avgs.append(sum(percents) / len(percents))
        except Exception:
            pass

        if not mode_avgs:
            return 0.0
        overall = sum(mode_avgs) / len(mode_avgs)
        # Round to 1 decimal to match UI formatting
        return round(overall, 1)

    def get_speaking_score(self, obj):
        """Speaking score from TopicProgress.conversation_total_score (0-100), averaged across topics."""
        user = obj.user
        try:
            tp_scores = list(
                TopicProgress.objects.filter(user=user).values_list('conversation_total_score', flat=True)
            )
            vals = [float(s or 0.0) for s in tp_scores]
            # Consider only topics with non-zero score; if none, return 0
            nonzero = [v for v in vals if v > 0.0]
            if nonzero:
                avg = sum(nonzero) / len(nonzero)
                return round(max(0.0, min(100.0, avg)), 1)
        except Exception:
            pass
        return 0.0

    def get_pronunciation_score(self, obj):
        """Pronunciation score from TopicProgress.pronunciation_total_score normalized by phrase count across topics (0-100)."""
        user = obj.user
        try:
            total_sum = 0.0
            total_count = 0
            for tp in TopicProgress.objects.filter(user=user).select_related('topic').only('pronunciation_total_score', 'topic__material_lines'):
                try:
                    phrase_count = len(tp.topic.material_lines or [])
                except Exception:
                    phrase_count = 0
                if phrase_count > 0 and (tp.pronunciation_total_score or 0) > 0:
                    total_sum += float(tp.pronunciation_total_score or 0.0)
                    total_count += phrase_count
            if total_count > 0:
                avg = total_sum / total_count  # 0..100
                return round(max(0.0, min(100.0, avg)), 1)
        except Exception:
            pass
        return 0.0

    def get_vocabulary_score(self, obj):
        """Vocabulary score from TopicProgress.vocabulary_total_score (0-100), averaged across topics with non-zero values."""
        user = obj.user
        try:
            tp_scores = list(
                TopicProgress.objects.filter(user=user).values_list('vocabulary_total_score', flat=True)
            )
            vals = [float(s or 0.0) for s in tp_scores]
            nonzero = [v for v in vals if v > 0.0]
            if nonzero:
                avg = sum(nonzero) / len(nonzero)
                return round(max(0.0, min(100.0, avg)), 1)
        except Exception:
            pass
        return 0.0

    def get_listening_score(self, obj):
        """Listening not implemented yet; return 0."""
        return 0.0

    def get_grammar_score(self, obj):
        """Grammar not implemented yet; return 0."""
        return 0.0

    def get_recent_achievements(self, obj):
        """Get the 3 most recent achievements earned by the user"""
        recent_badges = obj.user.earned_badges.select_related('badge').order_by('-earned_at')[:3]
        return UserBadgeSerializer(recent_badges, many=True).data

    def get_monthly_days_active(self, obj):
        """Get the number of days the user was active in the current month"""
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        _, last_day = monthrange(today.year, today.month)
        end_of_month = today.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

        # Count distinct dates with practice sessions
        return PracticeSession.objects.filter(
            user=obj.user,
            started_at__gte=start_of_month,
            started_at__lte=end_of_month,
            session_status='completed'
        ).dates('started_at', 'day').count()

    def get_monthly_xp_earned(self, obj):
        """Get the total XP earned by the user in the current month"""
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        _, last_day = monthrange(today.year, today.month)
        end_of_month = today.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

        # Calculate XP from completed practice sessions (assume 10-50 XP per session based on score)
        monthly_sessions = PracticeSession.objects.filter(
            user=obj.user,
            started_at__gte=start_of_month,
            started_at__lte=end_of_month,
            session_status='completed'
        )

        total_xp = 0
        for session in monthly_sessions:
            # Base XP calculation: 10 XP + bonus based on overall_score
            base_xp = 10
            if session.overall_score:
                bonus_xp = int(session.overall_score * 0.4)  # Up to 40 XP bonus for perfect score
                total_xp += base_xp + bonus_xp
            else:
                total_xp += base_xp

        return total_xp

    def get_monthly_lessons_completed(self, obj):
        """Number of Speaking Journey topics completed in the current month."""
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        _, last_day = monthrange(today.year, today.month)
        end_of_month = today.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

        # Count Speaking Journey TopicProgress completed within current month
        return TopicProgress.objects.filter(
            user=obj.user,
            completed=True,
            completed_at__gte=start_of_month,
            completed_at__lte=end_of_month
        ).count()

    def get_recent_activities(self, obj):
        """Get a unified feed of recent user activities"""
        activities = []

        # Get recent practice sessions (last 10)
        recent_sessions = PracticeSession.objects.filter(
            user=obj.user,
            session_status='completed'
        ).order_by('-completed_at')[:10]

        for session in recent_sessions:
            activity = {
                'type': 'practice_session',
                'title': f"Practiced {session.scenario_title or session.session_type.replace('_', ' ').title()}",
                'timestamp': session.completed_at,
                'icon': 'mic',
                'color': '#1976D2'  # Material Blue
            }
            activities.append(activity)

        # Get recent completed modules/lessons (last 10)
        recent_completions = UserProgress.objects.filter(
            user=obj.user,
            status='completed'
        ).select_related('learning_path', 'module', 'activity').order_by('-completed_at')[:10]

        for completion in recent_completions:
            if completion.module:
                title = f"Completed {completion.module.name}"
            elif completion.activity:
                title = f"Completed {completion.activity.name}"
            else:
                title = f"Completed {completion.learning_path.name} activity"

            activity = {
                'type': 'module_completion',
                'title': title,
                'timestamp': completion.completed_at,
                'icon': 'check_circle',
                'color': '#4CAF50'  # Material Green
            }
            activities.append(activity)

        # Get recent badges earned (last 5)
        recent_badges = obj.user.earned_badges.select_related('badge').order_by('-earned_at')[:5]

        for user_badge in recent_badges:
            activity = {
                'type': 'badge_earned',
                'title': f"Earned '{user_badge.badge.name}' badge",
                'timestamp': user_badge.earned_at,
                'icon': 'emoji_events',
                'color': '#FFD700'  # Gold
            }
            activities.append(activity)

        # Get recent learning path starts (last 3)
        recent_paths = obj.user.learning_paths.filter(
            started_at__isnull=False
        ).order_by('-started_at')[:3]

        for path in recent_paths:
            activity = {
                'type': 'path_started',
                'title': f"Started {path.name}",
                'timestamp': path.started_at,
                'icon': 'school',
                'color': '#9C27B0'  # Material Purple
            }
            activities.append(activity)

        # Sort all activities by timestamp (most recent first) and return top 10
        activities.sort(key=lambda x: x['timestamp'] if x['timestamp'] else timezone.now(), reverse=True)

        # Convert timestamps to relative time strings and return top 10
        for activity in activities[:10]:
            if activity['timestamp']:
                activity['relative_time'] = self._get_relative_time(activity['timestamp'])
            else:
                activity['relative_time'] = 'Unknown'
            # Remove the raw timestamp from the response
            del activity['timestamp']

        return activities[:10]

    def get_membership_status(self, obj):
        """Determine membership status based on user activity and level"""
        if hasattr(obj.user, 'level_profile'):
            level = obj.user.level_profile.current_level or 0
            if level >= 20:
                return "Premium Member"
            elif level >= 10:
                return "Gold Member"
            elif level >= 5:
                return "Silver Member"
            else:
                return "Bronze Member"
        return "New Member"

    def get_displayName(self, obj):
        """Generate display name from first_name + last_name or fallback to username"""
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.username or "User"
        
    def get_xpToNextLevel(self, obj):
        """Calculate XP needed to reach next level (Option A)."""
        lvl = getattr(obj.user, 'level_profile', None)
        if lvl:
            try:
                current_level = int(lvl.current_level or 1)
            except Exception:
                current_level = 1
            try:
                current_xp_val = int(lvl.experience_points or 0)
            except Exception:
                current_xp_val = 0
            required = max(1, 100 + 25 * (current_level - 1))
            return max(0, required - current_xp_val)
        return 100
        
    def get_longestStreak(self, obj):
        """Get longest streak - for now return current streak"""
        if hasattr(obj.user, 'level_profile') and obj.user.level_profile.streak_days:
            return obj.user.level_profile.streak_days
        return 0
        
    def get_stats(self, obj):
        """Generate UserStats object"""
        try:
            followers_count = UserFollow.objects.filter(following=obj.user).count()
        except Exception:
            followers_count = 0
        try:
            following_count = UserFollow.objects.filter(follower=obj.user).count()
        except Exception:
            following_count = 0

        return {
            'totalPracticeSessions': getattr(obj.user, 'analytics', None) and obj.user.analytics.total_sessions_completed or 0,
            'totalPracticeMinutes': getattr(obj.user, 'analytics', None) and obj.user.analytics.total_practice_time_minutes or 0,
            'averageAccuracy': 0.0,
            'averageFluency': getattr(obj.user, 'analytics', None) and obj.user.analytics.fluency_score or 0.0,
            'completedLessons': getattr(obj.user, 'analytics', None) and obj.user.analytics.scenarios_completed or 0,
            'achievementsUnlocked': obj.user.earned_badges.count(),
            'followersCount': followers_count,
            'followingCount': following_count,
            'globalRank': None,
            'weeklyXp': 0,
            'monthlyXp': 0,
            'totalWords': 0,
            'improvementRate': 0.0
        }

    def get_isFollowing(self, obj):
        """Return True if the requesting user follows the profile's user."""
        request = self.context.get('request')
        try:
            if request is None or not request.user.is_authenticated:
                return False
            if request.user == obj.user:
                return False
            return UserFollow.objects.filter(follower=request.user, following=obj.user).exists()
        except Exception:
            return False

    def get_isFollower(self, obj):
        """Return True if the profile's user follows the requesting user."""
        request = self.context.get('request')
        try:
            if request is None or not request.user.is_authenticated:
                return False
            if request.user == obj.user:
                return False
            return UserFollow.objects.filter(follower=obj.user, following=request.user).exists()
        except Exception:
            return False
        
    def get_badges(self, obj):
        """Get user badges"""
        return []
        
    def get_preferences(self, obj):
        """Generate UserPreferences object"""
        return {
            'dailyGoalMinutes': obj.daily_practice_goal or 15,
            'practiceRemindersEnabled': obj.enable_reminders or True,
            'reminderTime': None,
            'soundEffectsEnabled': True,
            'vibrationEnabled': True,
            'darkModeEnabled': False,
            'autoPlayAudio': True,
            'showPronunciationGuide': True,
            'difficulty': 'INTERMEDIATE',
            'focusAreas': [],
            'privacy': {
                'profileVisibility': 'PUBLIC',
                'showOnlineStatus': True,
                'showAchievements': True,
                'showStatistics': True,
                'allowFriendRequests': True,
                'allowMessages': True,
                'allowChallenges': True
            }
        }

    def get_avatar_url(self, obj):
        """Return absolute URL to uploaded avatar if present, otherwise fallback to stored URL string.
        This ensures clients can always render a usable avatar URL."""
        request = self.context.get('request')
        try:
            if obj.avatar and hasattr(obj.avatar, 'url'):
                # Build absolute URL for media file
                if request is not None:
                    return request.build_absolute_uri(obj.avatar.url)
                return obj.avatar.url
        except Exception:
            pass
        # Fallback to legacy avatar_url field (might be external URL)
        return obj.avatar_url or None

    def _get_relative_time(self, timestamp):
        """Convert timestamp to relative time string"""
        if not timestamp:
            return 'Unknown'

        now = timezone.now()
        diff = now - timestamp

        if diff.days > 7:
            return f"{diff.days // 7} week{'s' if diff.days // 7 > 1 else ''} ago"
        elif diff.days > 0:
            if diff.days == 1:
                return "Yesterday"
            else:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_email', 'username', 'email', 'displayName', 'first_name', 'last_name',
            'level', 'xp', 'xpToNextLevel', 'streakDays', 'longestStreak', 'joinedDate', 'lastActiveDate',
            'language', 'isVerified', 'isPremium', 'isOnline', 'isFollowing', 'isFollower', 'isBlocked',
            'followersCount', 'followingCount',
            'stats', 'badges', 'preferences',
            'date_of_birth', 'phone_number', 'avatar', 'avatar_url', 'bio',
            'native_language', 'target_language', 'current_proficiency',
            'learning_goal', 'daily_practice_goal', 'preferred_session_duration',
            'power_distance_preference', 'individualism_preference',
            'masculinity_preference', 'uncertainty_avoidance_preference',
            'long_term_orientation_preference',
            'preferred_reward_type', 'enable_notifications', 'enable_reminders',
            'total_practice_time', 'current_level', 'experience_points', 'total_points_earned', 'streak_days',
            'total_practice_hours', 'lessons_completed', 'recordings_count', 'avg_score',
            'daily_practice_goal', 'learning_goal', 'target_language',
            'speaking_score', 'listening_score', 'grammar_score', 'vocabulary_score', 'pronunciation_score',
            'monthly_days_active', 'monthly_xp_earned', 'monthly_lessons_completed',
            'recent_activities', 'membership_status',
            'last_practice_date',
            'created_at', 'updated_at', 'recent_achievements'
        ]
        read_only_fields = ['id', 'user', 'total_practice_time', 'created_at', 'updated_at']

    def get_followersCount(self, obj):
        try:
            return UserFollow.objects.filter(following=obj.user).count()
        except Exception:
            return 0

    def get_followingCount(self, obj):
        try:
            return UserFollow.objects.filter(follower=obj.user).count()
        except Exception:
            return 0


class LearningPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for learning preferences
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = LearningPreference
        fields = [
            'id', 'user', 'user_email',
            'preferred_scenarios', 'avoided_topics',
            'visual_learning', 'auditory_learning', 'kinesthetic_learning',
            'immediate_correction', 'detailed_feedback', 'cultural_context',
            'ai_personality', 'difficulty_adaptation_speed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UserAchievementSerializer(serializers.ModelSerializer):
    """
    Serializer for user achievements
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserAchievement
        fields = [
            'id', 'user', 'user_email',
            'achievement_type', 'achievement_name', 'achievement_description',
            'category', 'points_earned', 'badge_image_url',
            'progress_current', 'progress_target', 'is_completed',
            'completion_percentage',
            'earned_at', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

    def get_completion_percentage(self, obj):
        """Calculate completion percentage"""
        if obj.progress_target == 0:
            return 0
        return min(100, int((obj.progress_current / obj.progress_target) * 100))


class UserStatsSerializer(serializers.Serializer):
    """
    Serializer for user statistics summary
    """
    total_practice_time = serializers.IntegerField()
    streak_days = serializers.IntegerField()
    current_proficiency = serializers.CharField()
    completed_achievements = serializers.IntegerField()
    total_points = serializers.IntegerField()
    last_practice_date = serializers.DateField(allow_null=True)

    class Meta:
        fields = '__all__'
