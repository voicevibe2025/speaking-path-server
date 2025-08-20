"""
Views for Learning Paths
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
import logging

from .models import (
    LearningPath,
    LearningModule,
    ModuleActivity,
    UserProgress,
    Milestone,
    UserMilestone
)
from .serializers import (
    LearningPathSerializer,
    LearningModuleSerializer,
    ModuleActivitySerializer,
    UserProgressSerializer,
    MilestoneSerializer,
    UserMilestoneSerializer,
    LearningPathCreateSerializer,
    PathRecommendationSerializer
)

logger = logging.getLogger(__name__)


class LearningPathViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing learning paths
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LearningPathSerializer

    def get_queryset(self):
        """
        Return learning paths for the current user
        """
        return LearningPath.objects.filter(
            user=self.request.user
        ).prefetch_related('modules', 'modules__activities')

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'create':
            return LearningPathCreateSerializer
        return LearningPathSerializer

    @action(detail=False, methods=['post'])
    def recommend(self, request):
        """
        Recommend learning paths based on user assessment
        """
        serializer = PathRecommendationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            # Generate recommendations based on user data
            recommendations = self._generate_recommendations(data)

            return Response({
                'recommendations': recommendations,
                'personalization_factors': {
                    'current_level': data['current_level'],
                    'target_level': data['target_level'],
                    'estimated_weeks': self._calculate_duration(
                        data['current_level'],
                        data['target_level'],
                        data['available_hours_per_week']
                    )
                }
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a learning path and deactivate others
        """
        learning_path = self.get_object()

        # Deactivate other paths for this user
        LearningPath.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(pk=learning_path.pk).update(is_active=False)

        # Activate this path
        learning_path.is_active = True
        learning_path.started_at = timezone.now()
        learning_path.save()

        # Unlock first module
        first_module = learning_path.modules.filter(order_index=0).first()
        if first_module:
            first_module.is_locked = False
            first_module.unlocked_at = timezone.now()
            first_module.save()

        serializer = self.get_serializer(learning_path)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        Get detailed progress for a learning path
        """
        learning_path = self.get_object()

        # Calculate overall progress
        modules = learning_path.modules.all()
        completed_modules = modules.filter(is_completed=True).count()
        total_modules = modules.count()

        # Get user progress records
        user_progress = UserProgress.objects.filter(
            user=request.user,
            learning_path=learning_path
        )

        return Response({
            'path_id': learning_path.path_id,
            'overall_progress': learning_path.progress_percentage,
            'modules_completed': completed_modules,
            'modules_total': total_modules,
            'current_module': learning_path.current_module_index,
            'time_spent_total': user_progress.aggregate(
                total=models.Sum('time_spent_minutes')
            )['total'] or 0,
            'average_score': user_progress.filter(
                score__isnull=False
            ).aggregate(avg=Avg('score'))['avg'] or 0,
            'milestones_achieved': UserMilestone.objects.filter(
                user=request.user,
                learning_path=learning_path
            ).count()
        })

    def _generate_recommendations(self, data):
        """
        Generate personalized path recommendations
        """
        recommendations = []

        # Map learning goals to path types
        goal_to_path_type = {
            'business': 'business',
            'academic': 'academic',
            'travel': 'conversational',
            'exam': 'exam_prep',
            'general': 'intermediate'
        }

        for goal in data['learning_goals']:
            path_type = goal_to_path_type.get(goal.lower(), 'custom')

            recommendations.append({
                'name': f"{goal.title()} English Path",
                'path_type': path_type,
                'difficulty_level': data['current_level'],
                'target_proficiency': data['target_level'],
                'estimated_duration_weeks': self._calculate_duration(
                    data['current_level'],
                    data['target_level'],
                    data['available_hours_per_week']
                ),
                'focus_areas': self._determine_focus_areas(goal),
                'cultural_context': {
                    'indonesian_adaptation': True,
                    'cultural_scenarios': True,
                    'local_examples': True
                }
            })

        return recommendations

    def _calculate_duration(self, current_level, target_level, hours_per_week):
        """
        Calculate estimated duration in weeks
        """
        level_map = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
        level_diff = level_map[target_level] - level_map[current_level]

        # Approximate hours needed per level
        hours_per_level = 100
        total_hours = level_diff * hours_per_level

        return max(4, int(total_hours / hours_per_week))

    def _determine_focus_areas(self, goal):
        """
        Determine focus areas based on learning goal
        """
        focus_map = {
            'business': ['vocabulary', 'fluency', 'cultural'],
            'academic': ['grammar', 'vocabulary', 'fluency'],
            'travel': ['pronunciation', 'fluency', 'cultural'],
            'exam': ['grammar', 'vocabulary', 'listening'],
            'general': ['pronunciation', 'grammar', 'fluency']
        }

        return focus_map.get(goal.lower(), ['pronunciation', 'grammar', 'fluency'])


class LearningModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing learning modules
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LearningModuleSerializer

    def get_queryset(self):
        """
        Return modules for user's learning paths
        """
        return LearningModule.objects.filter(
            learning_path__user=self.request.user
        ).prefetch_related('activities')

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Start a learning module
        """
        module = self.get_object()

        if module.is_locked:
            return Response(
                {'error': 'Module is locked'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update module status
        module.started_at = timezone.now()
        module.save()

        # Create or update user progress
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            learning_path=module.learning_path,
            module=module,
            defaults={'status': 'in_progress'}
        )

        if not created and progress.status == 'not_started':
            progress.status = 'in_progress'
            progress.save()

        serializer = self.get_serializer(module)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete a learning module
        """
        module = self.get_object()
        score = request.data.get('score', 0)

        # Update module completion
        module.is_completed = True
        module.completed_at = timezone.now()
        module.completion_percentage = 100
        module.save()

        # Update user progress
        progress = UserProgress.objects.filter(
            user=request.user,
            learning_path=module.learning_path,
            module=module
        ).first()

        if progress:
            progress.status = 'completed'
            progress.score = score
            progress.completed_at = timezone.now()
            progress.save()

        # Unlock next module
        next_module = LearningModule.objects.filter(
            learning_path=module.learning_path,
            order_index=module.order_index + 1
        ).first()

        if next_module:
            next_module.is_locked = False
            next_module.unlocked_at = timezone.now()
            next_module.save()

        # Check for milestone achievements
        self._check_milestones(request.user, module.learning_path)

        return Response({
            'module_completed': True,
            'next_module_unlocked': next_module is not None,
            'score': score
        })

    def _check_milestones(self, user, learning_path):
        """
        Check and award milestones
        """
        # Check module completion milestones
        completed_modules = learning_path.modules.filter(is_completed=True).count()
        total_modules = learning_path.modules.count()

        if completed_modules == total_modules:
            # Path completion milestone
            milestone = Milestone.objects.filter(
                learning_path=learning_path,
                milestone_type='path_completion'
            ).first()

            if milestone:
                UserMilestone.objects.get_or_create(
                    user=user,
                    milestone=milestone,
                    learning_path=learning_path
                )


class ModuleActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing module activities
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ModuleActivitySerializer

    def get_queryset(self):
        """
        Return activities for user's modules
        """
        return ModuleActivity.objects.filter(
            module__learning_path__user=self.request.user
        )

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit activity completion
        """
        activity = self.get_object()
        results = request.data.get('results', {})

        # Create or update progress
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            learning_path=activity.module.learning_path,
            module=activity.module,
            activity=activity,
            defaults={
                'status': 'in_progress',
                'results': results
            }
        )

        if not created:
            progress.results = results
            progress.attempts += 1
            progress.save()

        # If requires AI evaluation, trigger it
        if activity.requires_ai_evaluation:
            # This would integrate with ai_evaluation app
            return Response({
                'submitted': True,
                'requires_ai_evaluation': True,
                'evaluation_pending': True
            })

        return Response({
            'submitted': True,
            'results_saved': True
        })


class UserProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tracking user progress
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProgressSerializer

    def get_queryset(self):
        """
        Return progress records for current user
        """
        return UserProgress.objects.filter(
            user=self.request.user
        ).select_related('learning_path', 'module', 'activity')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get overall progress summary for user
        """
        progress_records = self.get_queryset()

        return Response({
            'total_activities': progress_records.count(),
            'completed_activities': progress_records.filter(
                status='completed'
            ).count(),
            'in_progress_activities': progress_records.filter(
                status='in_progress'
            ).count(),
            'average_score': progress_records.filter(
                score__isnull=False
            ).aggregate(avg=Avg('score'))['avg'] or 0,
            'total_time_spent': progress_records.aggregate(
                total=models.Sum('time_spent_minutes')
            )['total'] or 0,
            'active_paths': LearningPath.objects.filter(
                user=request.user,
                is_active=True
            ).count()
        })


class MilestoneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing milestones
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MilestoneSerializer

    def get_queryset(self):
        """
        Return all available milestones
        """
        return Milestone.objects.all()


class UserMilestoneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user achievements
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserMilestoneSerializer

    def get_queryset(self):
        """
        Return achievements for current user
        """
        return UserMilestone.objects.filter(
            user=self.request.user
        ).select_related('milestone', 'learning_path')

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent achievements
        """
        recent_achievements = self.get_queryset()[:5]
        serializer = self.get_serializer(recent_achievements, many=True)
        return Response(serializer.data)
