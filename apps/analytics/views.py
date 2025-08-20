"""
Views for Analytics app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from .models import (
    UserAnalytics,
    SessionAnalytics,
    LearningProgress,
    ErrorPattern,
    SkillAssessment
)
from .serializers import (
    UserAnalyticsSerializer,
    SessionAnalyticsSerializer,
    SessionAnalyticsCreateSerializer,
    LearningProgressSerializer,
    ErrorPatternSerializer,
    SkillAssessmentSerializer,
    ProgressSummarySerializer,
    AnalyticsDashboardSerializer
)


class UserAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet for UserAnalytics"""
    serializer_class = UserAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get user's analytics"""
        return UserAnalytics.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_analytics(self, request):
        """Get current user's analytics"""
        analytics, created = UserAnalytics.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(analytics)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def update_streak(self, request):
        """Update user's practice streak"""
        analytics, _ = UserAnalytics.objects.get_or_create(user=request.user)

        today = timezone.now().date()

        # Check if user already practiced today
        if analytics.last_practice_date == today:
            return Response({
                'message': 'Already practiced today',
                'current_streak': analytics.current_streak_days
            })

        # Check if streak continues or resets
        if analytics.last_practice_date:
            days_diff = (today - analytics.last_practice_date).days
            if days_diff == 1:
                # Continue streak
                analytics.current_streak_days += 1
            elif days_diff > 1:
                # Reset streak
                analytics.current_streak_days = 1
        else:
            analytics.current_streak_days = 1

        # Update longest streak if needed
        if analytics.current_streak_days > analytics.longest_streak_days:
            analytics.longest_streak_days = analytics.current_streak_days

        analytics.last_practice_date = today
        analytics.save()

        return Response({
            'message': 'Streak updated',
            'current_streak': analytics.current_streak_days,
            'longest_streak': analytics.longest_streak_days
        })

    @action(detail=False, methods=['get'])
    def progress_chart(self, request):
        """Get data for progress chart"""
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        progress_data = LearningProgress.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        ).order_by('date').values(
            'date',
            'practice_time_minutes',
            'avg_pronunciation_score',
            'avg_fluency_score',
            'avg_vocabulary_score',
            'avg_grammar_score',
            'avg_coherence_score'
        )

        return Response({
            'period': f'{days} days',
            'data': list(progress_data)
        })

    @action(detail=False, methods=['get'])
    def skill_comparison(self, request):
        """Compare user's skills with averages"""
        analytics, _ = UserAnalytics.objects.get_or_create(user=request.user)

        # Get average scores across all users
        avg_scores = UserAnalytics.objects.aggregate(
            avg_pronunciation=Avg('pronunciation_score'),
            avg_fluency=Avg('fluency_score'),
            avg_vocabulary=Avg('vocabulary_score'),
            avg_grammar=Avg('grammar_score'),
            avg_coherence=Avg('coherence_score')
        )

        return Response({
            'user_scores': {
                'pronunciation': analytics.pronunciation_score,
                'fluency': analytics.fluency_score,
                'vocabulary': analytics.vocabulary_score,
                'grammar': analytics.grammar_score,
                'coherence': analytics.coherence_score
            },
            'average_scores': {
                'pronunciation': round(avg_scores['avg_pronunciation'] or 0, 2),
                'fluency': round(avg_scores['avg_fluency'] or 0, 2),
                'vocabulary': round(avg_scores['avg_vocabulary'] or 0, 2),
                'grammar': round(avg_scores['avg_grammar'] or 0, 2),
                'coherence': round(avg_scores['avg_coherence'] or 0, 2)
            }
        })


class SessionAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet for SessionAnalytics"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SessionAnalyticsCreateSerializer
        return SessionAnalyticsSerializer

    def get_queryset(self):
        """Get user's session analytics"""
        return SessionAnalytics.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Create session analytics and update user analytics"""
        session_analytics = serializer.save(user=self.request.user)

        # Update user analytics
        user_analytics, _ = UserAnalytics.objects.get_or_create(
            user=self.request.user
        )

        # Update totals
        user_analytics.total_sessions_completed += 1
        user_analytics.total_practice_time_minutes += session_analytics.duration_seconds / 60

        # Update average duration
        user_analytics.average_session_duration_minutes = (
            user_analytics.total_practice_time_minutes /
            user_analytics.total_sessions_completed
        )

        # Update scores (weighted average with recent sessions)
        recent_sessions = SessionAnalytics.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:10]

        if recent_sessions:
            user_analytics.pronunciation_score = recent_sessions.aggregate(
                avg=Avg('pronunciation_score'))['avg'] or 0
            user_analytics.fluency_score = recent_sessions.aggregate(
                avg=Avg('fluency_score'))['avg'] or 0
            user_analytics.vocabulary_score = recent_sessions.aggregate(
                avg=Avg('vocabulary_score'))['avg'] or 0
            user_analytics.grammar_score = recent_sessions.aggregate(
                avg=Avg('grammar_score'))['avg'] or 0
            user_analytics.coherence_score = recent_sessions.aggregate(
                avg=Avg('coherence_score'))['avg'] or 0
            user_analytics.overall_proficiency_score = recent_sessions.aggregate(
                avg=Avg('overall_score'))['avg'] or 0

        user_analytics.save()

        # Update daily progress
        today = timezone.now().date()
        daily_progress, _ = LearningProgress.objects.get_or_create(
            user=self.request.user,
            date=today,
            defaults={
                'week_number': today.isocalendar()[1],
                'month': today.month,
                'year': today.year
            }
        )

        daily_progress.practice_time_minutes += session_analytics.duration_seconds / 60
        daily_progress.sessions_count += 1
        daily_progress.words_practiced += session_analytics.total_words

        # Update daily averages
        today_sessions = SessionAnalytics.objects.filter(
            user=self.request.user,
            created_at__date=today
        )

        daily_progress.avg_pronunciation_score = today_sessions.aggregate(
            avg=Avg('pronunciation_score'))['avg'] or 0
        daily_progress.avg_fluency_score = today_sessions.aggregate(
            avg=Avg('fluency_score'))['avg'] or 0
        daily_progress.avg_vocabulary_score = today_sessions.aggregate(
            avg=Avg('vocabulary_score'))['avg'] or 0
        daily_progress.avg_grammar_score = today_sessions.aggregate(
            avg=Avg('grammar_score'))['avg'] or 0
        daily_progress.avg_coherence_score = today_sessions.aggregate(
            avg=Avg('coherence_score'))['avg'] or 0

        # Check if daily goal achieved
        if daily_progress.practice_time_minutes >= daily_progress.daily_goal_minutes:
            daily_progress.goal_achieved = True

        daily_progress.save()

    @action(detail=False, methods=['get'])
    def session_history(self, request):
        """Get session history with filters"""
        days = int(request.query_params.get('days', 7))
        session_type = request.query_params.get('type', None)

        queryset = self.get_queryset()

        # Apply filters
        if days:
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(created_at__gte=start_date)

        if session_type:
            queryset = queryset.filter(session_type=session_type)

        # Get summary statistics
        summary = queryset.aggregate(
            total_sessions=Count('id'),
            total_time=Sum('duration_seconds'),
            avg_score=Avg('overall_score'),
            avg_duration=Avg('duration_seconds')
        )

        serializer = self.get_serializer(queryset[:20], many=True)

        return Response({
            'summary': {
                'total_sessions': summary['total_sessions'] or 0,
                'total_time_minutes': round((summary['total_time'] or 0) / 60, 2),
                'average_score': round(summary['avg_score'] or 0, 2),
                'average_duration_minutes': round((summary['avg_duration'] or 0) / 60, 2)
            },
            'sessions': serializer.data
        })

    @action(detail=True, methods=['get'])
    def detailed_feedback(self, request, pk=None):
        """Get detailed feedback for a session"""
        session = self.get_object()

        # Generate detailed feedback based on scores
        feedback = {
            'overall_performance': self._get_performance_level(session.overall_score),
            'strengths': [],
            'improvements_needed': [],
            'specific_feedback': {}
        }

        # Analyze each skill
        skills = {
            'pronunciation': session.pronunciation_score,
            'fluency': session.fluency_score,
            'vocabulary': session.vocabulary_score,
            'grammar': session.grammar_score,
            'coherence': session.coherence_score
        }

        for skill, score in skills.items():
            if score >= 70:
                feedback['strengths'].append(skill)
            elif score < 50:
                feedback['improvements_needed'].append(skill)

            feedback['specific_feedback'][skill] = {
                'score': score,
                'level': self._get_performance_level(score),
                'tips': self._get_improvement_tips(skill, score)
            }

        return Response(feedback)

    def _get_performance_level(self, score):
        """Get performance level based on score"""
        if score >= 90:
            return 'Excellent'
        elif score >= 75:
            return 'Good'
        elif score >= 60:
            return 'Satisfactory'
        elif score >= 45:
            return 'Needs Improvement'
        else:
            return 'Poor'

    def _get_improvement_tips(self, skill, score):
        """Get improvement tips based on skill and score"""
        tips = {
            'pronunciation': [
                'Practice minimal pairs',
                'Record yourself and compare with native speakers',
                'Focus on problematic sounds'
            ],
            'fluency': [
                'Practice speaking without pausing',
                'Use filler phrases appropriately',
                'Read aloud daily'
            ],
            'vocabulary': [
                'Learn new words in context',
                'Use vocabulary in sentences',
                'Practice word families'
            ],
            'grammar': [
                'Review grammar rules',
                'Practice sentence structures',
                'Focus on common errors'
            ],
            'coherence': [
                'Use linking words',
                'Organize thoughts before speaking',
                'Practice structured responses'
            ]
        }

        if score < 50:
            return tips.get(skill, [])[:3]
        elif score < 70:
            return tips.get(skill, [])[:2]
        else:
            return tips.get(skill, [])[:1]


class LearningProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for LearningProgress"""
    serializer_class = LearningProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get user's learning progress"""
        return LearningProgress.objects.filter(
            user=self.request.user
        ).order_by('-date')

    @action(detail=False, methods=['get'])
    def weekly_summary(self, request):
        """Get weekly learning summary"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)

        progress = self.get_queryset().filter(
            date__range=[start_date, end_date]
        )

        summary = progress.aggregate(
            total_time=Sum('practice_time_minutes'),
            total_sessions=Sum('sessions_count'),
            total_words=Sum('words_practiced'),
            avg_pronunciation=Avg('avg_pronunciation_score'),
            avg_fluency=Avg('avg_fluency_score'),
            avg_vocabulary=Avg('avg_vocabulary_score'),
            avg_grammar=Avg('avg_grammar_score'),
            avg_coherence=Avg('avg_coherence_score')
        )

        # Calculate goal achievement rate
        goal_days = progress.filter(goal_achieved=True).count()
        total_days = progress.count()
        goal_achievement_rate = (goal_days / total_days * 100) if total_days > 0 else 0

        return Response({
            'period': 'Last 7 days',
            'summary': {
                'total_practice_time': summary['total_time'] or 0,
                'total_sessions': summary['total_sessions'] or 0,
                'total_words_practiced': summary['total_words'] or 0,
                'goal_achievement_rate': round(goal_achievement_rate, 2),
                'average_scores': {
                    'pronunciation': round(summary['avg_pronunciation'] or 0, 2),
                    'fluency': round(summary['avg_fluency'] or 0, 2),
                    'vocabulary': round(summary['avg_vocabulary'] or 0, 2),
                    'grammar': round(summary['avg_grammar'] or 0, 2),
                    'coherence': round(summary['avg_coherence'] or 0, 2)
                }
            },
            'daily_progress': LearningProgressSerializer(progress, many=True).data
        })

    @action(detail=False, methods=['post'])
    def set_daily_goal(self, request):
        """Set daily practice goal"""
        goal_minutes = request.data.get('goal_minutes', 30)

        if goal_minutes < 5 or goal_minutes > 180:
            return Response({
                'error': 'Goal must be between 5 and 180 minutes'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update today's goal
        today = timezone.now().date()
        progress, _ = LearningProgress.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={
                'week_number': today.isocalendar()[1],
                'month': today.month,
                'year': today.year
            }
        )

        progress.daily_goal_minutes = goal_minutes
        progress.save()

        return Response({
            'message': 'Daily goal updated',
            'goal_minutes': goal_minutes
        })


class ErrorPatternViewSet(viewsets.ModelViewSet):
    """ViewSet for ErrorPattern"""
    serializer_class = ErrorPatternSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get user's error patterns"""
        return ErrorPattern.objects.filter(
            user=self.request.user,
            is_resolved=False
        ).order_by('-occurrence_count')

    @action(detail=False, methods=['get'])
    def common_errors(self, request):
        """Get most common error patterns"""
        error_type = request.query_params.get('type', None)

        queryset = self.get_queryset()
        if error_type:
            queryset = queryset.filter(error_type=error_type)

        # Get top 10 most common errors
        top_errors = queryset[:10]

        return Response({
            'total_patterns': queryset.count(),
            'top_errors': ErrorPatternSerializer(top_errors, many=True).data
        })

    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        """Mark an error pattern as resolved"""
        error_pattern = self.get_object()
        error_pattern.is_resolved = True
        error_pattern.resolved_date = timezone.now()
        error_pattern.save()

        return Response({
            'message': 'Error pattern marked as resolved'
        })

    @action(detail=False, methods=['get'])
    def improvement_focus(self, request):
        """Get prioritized errors to focus on"""
        # Get unresolved errors with high impact
        high_impact_errors = self.get_queryset().filter(
            impact_on_communication__gte=0.5,
            severity_level__gte=3
        ).order_by('-occurrence_count')[:5]

        # Get frequently occurring errors
        frequent_errors = self.get_queryset().order_by('-occurrence_count')[:5]

        # Combine and deduplicate
        focus_errors = list(high_impact_errors) + list(frequent_errors)
        focus_errors = list({e.pattern_id: e for e in focus_errors}.values())[:5]

        return Response({
            'focus_areas': ErrorPatternSerializer(focus_errors, many=True).data,
            'recommendations': self._get_error_recommendations(focus_errors)
        })

    def _get_error_recommendations(self, errors):
        """Get recommendations based on error patterns"""
        recommendations = []

        for error in errors:
            if error.error_type == 'pronunciation':
                recommendations.append(
                    f"Practice pronunciation of: {', '.join(error.example_errors[:3])}"
                )
            elif error.error_type == 'grammar':
                recommendations.append(
                    f"Review grammar rule: {error.error_pattern}"
                )
            elif error.error_type == 'vocabulary':
                recommendations.append(
                    f"Expand vocabulary related to: {error.error_pattern}"
                )

        return recommendations[:3]


class SkillAssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for SkillAssessment"""
    serializer_class = SkillAssessmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get user's skill assessments"""
        return SkillAssessment.objects.filter(
            user=self.request.user
        ).order_by('-assessment_date')

    def perform_create(self, serializer):
        """Create skill assessment and update user analytics"""
        assessment = serializer.save(user=self.request.user)

        # Update user analytics with latest assessment
        user_analytics, _ = UserAnalytics.objects.get_or_create(
            user=self.request.user
        )

        # If this is the first assessment, set as initial
        if not user_analytics.initial_proficiency_score:
            user_analytics.initial_proficiency_score = assessment.overall_score

        # Update current scores
        user_analytics.overall_proficiency_score = assessment.overall_score
        user_analytics.pronunciation_score = assessment.pronunciation_score
        user_analytics.fluency_score = assessment.fluency_score
        user_analytics.vocabulary_score = assessment.vocabulary_score
        user_analytics.grammar_score = assessment.grammar_score
        user_analytics.coherence_score = assessment.coherence_score

        # Calculate improvement rate
        user_analytics.improvement_rate = user_analytics.calculate_improvement_rate()
        user_analytics.save()

    @action(detail=False, methods=['get'])
    def latest_assessment(self, request):
        """Get latest skill assessment"""
        latest = self.get_queryset().first()

        if not latest:
            return Response({
                'message': 'No assessments found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(latest)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def progress_timeline(self, request):
        """Get assessment progress over time"""
        assessments = self.get_queryset()[:10]

        timeline_data = []
        for assessment in assessments:
            timeline_data.append({
                'date': assessment.assessment_date,
                'type': assessment.assessment_type,
                'overall_score': assessment.overall_score,
                'proficiency_level': assessment.proficiency_level,
                'improvement': assessment.improvement_from_last
            })

        return Response({
            'timeline': timeline_data,
            'total_assessments': assessments.count()
        })


class AnalyticsDashboardViewSet(viewsets.ViewSet):
    """ViewSet for analytics dashboard"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get comprehensive analytics dashboard"""
        user = request.user

        # Get user analytics
        user_analytics, _ = UserAnalytics.objects.get_or_create(user=user)

        # Get recent sessions (last 5)
        recent_sessions = SessionAnalytics.objects.filter(
            user=user
        ).order_by('-created_at')[:5]

        # Get weekly progress
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        weekly_progress = LearningProgress.objects.filter(
            user=user,
            date__range=[start_date, end_date]
        ).order_by('-date')

        # Get active error patterns
        active_errors = ErrorPattern.objects.filter(
            user=user,
            is_resolved=False
        ).order_by('-occurrence_count')[:5]

        # Get latest assessment
        latest_assessment = SkillAssessment.objects.filter(
            user=user
        ).order_by('-assessment_date').first()

        # Calculate progress summary
        progress_summary = self._calculate_progress_summary(
            user, weekly_progress, recent_sessions
        )

        # Prepare dashboard data
        dashboard_data = {
            'user_analytics': user_analytics,
            'recent_sessions': recent_sessions,
            'weekly_progress': weekly_progress,
            'active_error_patterns': active_errors,
            'latest_assessment': latest_assessment,
            'progress_summary': progress_summary
        }

        serializer = AnalyticsDashboardSerializer(dashboard_data)
        return Response(serializer.data)

    def _calculate_progress_summary(self, user, weekly_progress, recent_sessions):
        """Calculate progress summary statistics"""
        # Calculate weekly totals
        weekly_stats = weekly_progress.aggregate(
            total_time=Sum('practice_time_minutes'),
            total_sessions=Sum('sessions_count'),
            avg_score=Avg(
                (F('avg_pronunciation_score') +
                 F('avg_fluency_score') +
                 F('avg_vocabulary_score') +
                 F('avg_grammar_score') +
                 F('avg_coherence_score')) / 5
            )
        )

        # Get user analytics for streak
        user_analytics, _ = UserAnalytics.objects.get_or_create(user=user)

        # Identify top skills and areas to improve
        if recent_sessions:
            skill_avgs = recent_sessions.aggregate(
                pronunciation=Avg('pronunciation_score'),
                fluency=Avg('fluency_score'),
                vocabulary=Avg('vocabulary_score'),
                grammar=Avg('grammar_score'),
                coherence=Avg('coherence_score')
            )

            sorted_skills = sorted(skill_avgs.items(), key=lambda x: x[1] or 0, reverse=True)
            top_skills = [skill[0] for skill in sorted_skills[:2]]
            areas_to_improve = [skill[0] for skill in sorted_skills[-2:]]
        else:
            top_skills = []
            areas_to_improve = []

        return {
            'period': 'weekly',
            'total_practice_time': weekly_stats['total_time'] or 0,
            'total_sessions': weekly_stats['total_sessions'] or 0,
            'average_score': round(weekly_stats['avg_score'] or 0, 2),
            'improvement_rate': user_analytics.improvement_rate,
            'streak_days': user_analytics.current_streak_days,
            'achievements_earned': user_analytics.achievements_earned,
            'top_skills': top_skills,
            'areas_to_improve': areas_to_improve
        }
