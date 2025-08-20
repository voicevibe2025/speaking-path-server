"""
Views for Cultural Adaptation app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from .models import (
    CulturalProfile,
    CulturalScenario,
    CulturalFeedbackTemplate,
    IndonesianEnglishMapping,
    CulturalAdaptationPreference
)
from .serializers import (
    CulturalProfileSerializer,
    CulturalScenarioSerializer,
    CulturalFeedbackTemplateSerializer,
    IndonesianEnglishMappingSerializer,
    CulturalAdaptationPreferenceSerializer,
    CulturalContextSerializer,
    CulturalFeedbackRequestSerializer
)
import random


class CulturalProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user cultural profiles
    """
    serializer_class = CulturalProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter profiles based on user permissions"""
        if self.request.user.is_staff:
            return CulturalProfile.objects.all()
        return CulturalProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create profile for current user"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's cultural profile"""
        try:
            profile = CulturalProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except CulturalProfile.DoesNotExist:
            return Response(
                {"detail": "Cultural profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def calibrate_dimensions(self, request, pk=None):
        """
        Calibrate Hofstede's dimensions based on user responses
        """
        profile = self.get_object()

        # Calibration questions responses
        responses = request.data.get('responses', {})

        # Simple calibration logic (can be enhanced with ML)
        adjustments = {
            'power_distance_index': 0,
            'individualism_index': 0,
            'masculinity_index': 0,
            'uncertainty_avoidance_index': 0,
            'long_term_orientation_index': 0,
            'indulgence_index': 0
        }

        # Adjust based on responses
        if responses.get('prefers_hierarchy'):
            adjustments['power_distance_index'] += 10
        if responses.get('values_group_success'):
            adjustments['individualism_index'] -= 10
        if responses.get('prefers_competition'):
            adjustments['masculinity_index'] += 10
        if responses.get('likes_structure'):
            adjustments['uncertainty_avoidance_index'] += 10
        if responses.get('plans_long_term'):
            adjustments['long_term_orientation_index'] += 10
        if responses.get('values_freedom'):
            adjustments['indulgence_index'] += 10

        # Apply adjustments
        for dimension, adjustment in adjustments.items():
            current_value = getattr(profile, dimension)
            new_value = max(0, min(100, current_value + adjustment))
            setattr(profile, dimension, new_value)

        profile.save()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def regional_insights(self, request):
        """Get cultural insights for different regions"""
        region = request.query_params.get('region', 'jakarta')

        # Regional cultural tendencies (based on research)
        regional_data = {
            'jakarta': {
                'power_distance': 75,
                'individualism': 20,
                'english_exposure': 'moderate',
                'learning_preference': 'hybrid'
            },
            'bali': {
                'power_distance': 70,
                'individualism': 15,
                'english_exposure': 'frequent',
                'learning_preference': 'group'
            },
            'west_java': {
                'power_distance': 80,
                'individualism': 12,
                'english_exposure': 'minimal',
                'learning_preference': 'hierarchical'
            }
        }

        return Response(regional_data.get(region, regional_data['jakarta']))


class CulturalScenarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet for cultural scenarios
    """
    queryset = CulturalScenario.objects.filter(is_active=True)
    serializer_class = CulturalScenarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter scenarios based on user profile"""
        queryset = super().get_queryset()

        # Filter by context type if provided
        context_type = self.request.query_params.get('context_type')
        if context_type:
            queryset = queryset.filter(context_type=context_type)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)

        # Filter by formality
        formality = self.request.query_params.get('formality')
        if formality:
            queryset = queryset.filter(formality_level=formality)

        return queryset.order_by('difficulty_level', 'context_type')

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Get recommended scenarios for user"""
        try:
            profile = request.user.cultural_profile

            # Get scenarios matching user's region and level
            scenarios = CulturalScenario.objects.filter(
                Q(relevant_regions__contains=[profile.region]) |
                Q(relevant_regions=[])
            ).filter(is_active=True)

            # Filter by user's English exposure level
            if profile.english_exposure_level in ['none', 'minimal']:
                scenarios = scenarios.filter(difficulty_level__lte=2)
            elif profile.english_exposure_level == 'moderate':
                scenarios = scenarios.filter(difficulty_level__lte=3)

            # Get diverse context types
            context_types = scenarios.values_list('context_type', flat=True).distinct()
            recommended = []
            for context in context_types[:5]:  # Get top 5 different contexts
                scenario = scenarios.filter(context_type=context).first()
                if scenario:
                    recommended.append(scenario)

            serializer = self.get_serializer(recommended, many=True)
            return Response(serializer.data)

        except CulturalProfile.DoesNotExist:
            # Return general recommendations
            scenarios = CulturalScenario.objects.filter(
                difficulty_level__lte=2,
                is_active=True
            )[:5]
            serializer = self.get_serializer(scenarios, many=True)
            return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def cultural_tips(self, request, pk=None):
        """Get cultural tips for a specific scenario"""
        scenario = self.get_object()

        tips = {
            'scenario_id': scenario.scenario_id,
            'cultural_considerations': [],
            'language_tips': [],
            'behavioral_guidelines': []
        }

        # Add relevant cultural considerations
        if scenario.involves_hierarchy:
            tips['cultural_considerations'].append(
                "Remember to show respect to authority figures using appropriate titles"
            )
        if scenario.involves_face_saving:
            tips['cultural_considerations'].append(
                "Avoid direct criticism; use indirect language to maintain harmony"
            )
        if scenario.involves_indirect_communication:
            tips['language_tips'].append(
                "Pay attention to implied meanings and non-verbal cues"
            )
        if scenario.involves_group_harmony:
            tips['behavioral_guidelines'].append(
                "Prioritize group consensus over individual opinions"
            )

        # Add context-specific tips
        if scenario.context_type == 'formal_business':
            tips['language_tips'].append("Use formal pronouns and business vocabulary")
        elif scenario.context_type == 'marketplace':
            tips['behavioral_guidelines'].append("Bargaining is expected and part of the culture")

        tips['cultural_notes'] = scenario.cultural_notes

        return Response(tips)


class CulturalFeedbackTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for cultural feedback templates
    """
    queryset = CulturalFeedbackTemplate.objects.filter(is_active=True)
    serializer_class = CulturalFeedbackTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter templates based on parameters"""
        queryset = super().get_queryset()

        # Filter by feedback type
        feedback_type = self.request.query_params.get('feedback_type')
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)

        # Filter by user level
        if hasattr(self.request.user, 'user_level'):
            user_level = self.request.user.user_level.current_level
            queryset = queryset.filter(
                min_level__lte=user_level,
                max_level__gte=user_level
            )

        return queryset

    @action(detail=False, methods=['post'])
    def generate_feedback(self, request):
        """Generate culturally appropriate feedback"""
        serializer = CulturalFeedbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        feedback_type = serializer.validated_data['feedback_type']
        user_level = serializer.validated_data['user_level']
        performance_score = serializer.validated_data['performance_score']

        # Get appropriate template
        templates = CulturalFeedbackTemplate.objects.filter(
            feedback_type=feedback_type,
            min_level__lte=user_level,
            max_level__gte=user_level,
            is_active=True
        )

        if not templates:
            return Response(
                {"detail": "No appropriate feedback template found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Select random template for variety
        template = random.choice(templates)

        # Get user's preference
        try:
            preference = request.user.cultural_preferences
            language_pref = preference.feedback_language
        except:
            language_pref = 'mixed'

        # Prepare feedback based on language preference
        feedback_text = {
            'english': template.template_english,
            'indonesian': template.template_indonesian,
            'mixed': template.template_mixed,
            'adaptive': template.template_mixed if performance_score < 70 else template.template_english
        }.get(language_pref, template.template_mixed)

        # Customize feedback with performance data
        feedback_text = feedback_text.format(
            score=performance_score,
            level=user_level,
            improvement=100 - performance_score
        )

        return Response({
            'feedback': feedback_text,
            'template_id': template.template_id,
            'uses_indirect_language': template.uses_indirect_language,
            'includes_encouragement': template.includes_encouragement
        })


class IndonesianEnglishMappingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Indonesian-English interference patterns
    """
    queryset = IndonesianEnglishMapping.objects.filter(is_active=True)
    serializer_class = IndonesianEnglishMappingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter mappings based on parameters"""
        queryset = super().get_queryset()

        # Filter by interference type
        interference_type = self.request.query_params.get('type')
        if interference_type:
            queryset = queryset.filter(interference_type=interference_type)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)

        return queryset.order_by('-frequency_score', 'difficulty_level')

    @action(detail=False, methods=['get'])
    def common_errors(self, request):
        """Get most common errors for Indonesian speakers"""
        # Get top errors by frequency
        errors = IndonesianEnglishMapping.objects.filter(
            is_active=True,
            frequency_score__gte=0.7
        ).order_by('-frequency_score')[:10]

        serializer = self.get_serializer(errors, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def check_interference(self, request):
        """Check text for potential interference patterns"""
        text = request.data.get('text', '')

        if not text:
            return Response(
                {"detail": "Text is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find potential interference patterns
        found_patterns = []
        mappings = IndonesianEnglishMapping.objects.filter(is_active=True)

        for mapping in mappings:
            if mapping.common_error.lower() in text.lower():
                found_patterns.append({
                    'pattern': mapping.indonesian_pattern,
                    'error': mapping.common_error,
                    'correction': mapping.correct_form,
                    'explanation': mapping.explanation,
                    'type': mapping.interference_type
                })

        return Response({
            'text': text,
            'patterns_found': found_patterns,
            'count': len(found_patterns)
        })


class CulturalAdaptationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user cultural adaptation preferences
    """
    serializer_class = CulturalAdaptationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter preferences based on user"""
        if self.request.user.is_staff:
            return CulturalAdaptationPreference.objects.all()
        return CulturalAdaptationPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create preference for current user"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's preferences"""
        try:
            preferences = CulturalAdaptationPreference.objects.get(user=request.user)
            serializer = self.get_serializer(preferences)
            return Response(serializer.data)
        except CulturalAdaptationPreference.DoesNotExist:
            return Response(
                {"detail": "Preferences not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def update_learning_style(self, request):
        """Update learning style scores based on assessment"""
        try:
            preferences = CulturalAdaptationPreference.objects.get(user=request.user)
        except CulturalAdaptationPreference.DoesNotExist:
            preferences = CulturalAdaptationPreference.objects.create(user=request.user)

        # Update scores
        preferences.visual_learner_score = request.data.get('visual', 0.33)
        preferences.auditory_learner_score = request.data.get('auditory', 0.33)
        preferences.kinesthetic_learner_score = request.data.get('kinesthetic', 0.34)

        # Normalize scores
        total = (preferences.visual_learner_score +
                preferences.auditory_learner_score +
                preferences.kinesthetic_learner_score)

        if total > 0:
            preferences.visual_learner_score /= total
            preferences.auditory_learner_score /= total
            preferences.kinesthetic_learner_score /= total

        preferences.save()
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)
