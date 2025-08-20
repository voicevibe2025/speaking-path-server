"""
Serializers for Cultural Adaptation app
"""
from rest_framework import serializers
from .models import (
    CulturalProfile,
    CulturalScenario,
    CulturalFeedbackTemplate,
    IndonesianEnglishMapping,
    CulturalAdaptationPreference
)


class CulturalProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user's cultural profile
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)
    education_display = serializers.CharField(source='get_education_level_display', read_only=True)

    class Meta:
        model = CulturalProfile
        fields = [
            'id', 'user', 'user_email', 'region', 'region_display',
            'urban_rural', 'age_group', 'education_level', 'education_display',
            'profession_category', 'power_distance_index', 'individualism_index',
            'masculinity_index', 'uncertainty_avoidance_index',
            'long_term_orientation_index', 'indulgence_index',
            'primary_language', 'regional_language', 'english_exposure_level',
            'prefers_group_learning', 'prefers_hierarchical_structure',
            'needs_face_saving_feedback', 'values_relationship_building',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Validate cultural dimension indices are within range"""
        indices = [
            'power_distance_index', 'individualism_index', 'masculinity_index',
            'uncertainty_avoidance_index', 'long_term_orientation_index', 'indulgence_index'
        ]
        for index in indices:
            if index in attrs and not (0 <= attrs[index] <= 100):
                raise serializers.ValidationError(
                    f"{index} must be between 0 and 100"
                )
        return attrs


class CulturalScenarioSerializer(serializers.ModelSerializer):
    """
    Serializer for cultural speaking scenarios
    """
    context_display = serializers.CharField(source='get_context_type_display', read_only=True)
    formality_display = serializers.CharField(source='get_formality_level_display', read_only=True)
    is_suitable_for_user = serializers.SerializerMethodField()

    class Meta:
        model = CulturalScenario
        fields = [
            'id', 'scenario_id', 'title', 'title_indonesian',
            'description', 'description_indonesian', 'context_type',
            'context_display', 'formality_level', 'formality_display',
            'involves_hierarchy', 'involves_face_saving',
            'involves_indirect_communication', 'involves_group_harmony',
            'relevant_regions', 'example_phrases', 'cultural_notes',
            'difficulty_level', 'image_url', 'audio_example_url',
            'is_active', 'is_suitable_for_user', 'created_at'
        ]
        read_only_fields = ['scenario_id', 'created_at']

    def get_is_suitable_for_user(self, obj):
        """Check if scenario is suitable for current user's profile"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'cultural_profile'):
            profile = request.user.cultural_profile
            # Check if user's region is in relevant regions
            if obj.relevant_regions and profile.region in obj.relevant_regions:
                return True
            # Check if scenario matches user's context preferences
            if profile.education_level in ['s1', 's2', 's3'] and obj.context_type in ['formal_business', 'education', 'technology']:
                return True
        return False


class CulturalFeedbackTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for culturally appropriate feedback templates
    """
    is_applicable_to_user = serializers.SerializerMethodField()

    class Meta:
        model = CulturalFeedbackTemplate
        fields = [
            'id', 'template_id', 'feedback_type', 'template_english',
            'template_indonesian', 'template_mixed', 'uses_indirect_language',
            'includes_encouragement', 'avoids_direct_criticism',
            'min_level', 'max_level', 'regional_variations',
            'is_active', 'is_applicable_to_user', 'created_at'
        ]
        read_only_fields = ['template_id', 'created_at']

    def get_is_applicable_to_user(self, obj):
        """Check if template is applicable to current user's level"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'user_level'):
            user_level = request.user.user_level.current_level
            return obj.min_level <= user_level <= obj.max_level
        return True


class IndonesianEnglishMappingSerializer(serializers.ModelSerializer):
    """
    Serializer for Indonesian-English interference patterns
    """
    relevance_score = serializers.SerializerMethodField()

    class Meta:
        model = IndonesianEnglishMapping
        fields = [
            'id', 'mapping_id', 'indonesian_pattern', 'english_equivalent',
            'interference_type', 'common_error', 'correct_form',
            'explanation', 'explanation_indonesian', 'difficulty_level',
            'frequency_score', 'teaching_tips', 'practice_exercises',
            'relevance_score', 'is_active', 'created_at'
        ]
        read_only_fields = ['mapping_id', 'created_at']

    def get_relevance_score(self, obj):
        """Calculate relevance score based on user's profile"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'cultural_profile'):
            profile = request.user.cultural_profile
            # Higher relevance for users with lower English exposure
            exposure_weights = {
                'none': 1.0,
                'minimal': 0.8,
                'moderate': 0.6,
                'frequent': 0.4,
                'daily': 0.2
            }
            weight = exposure_weights.get(profile.english_exposure_level, 0.5)
            return obj.frequency_score * weight
        return obj.frequency_score


class CulturalAdaptationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for user's cultural adaptation preferences
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    learning_style_summary = serializers.SerializerMethodField()

    class Meta:
        model = CulturalAdaptationPreference
        fields = [
            'id', 'user', 'user_email', 'prefers_bilingual_instructions',
            'prefers_local_examples', 'prefers_religious_neutral_content',
            'feedback_language', 'feedback_formality',
            'prefers_individual_achievements', 'prefers_group_achievements',
            'prefers_competition', 'prefers_collaboration',
            'visual_learner_score', 'auditory_learner_score',
            'kinesthetic_learner_score', 'learning_style_summary',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_learning_style_summary(self, obj):
        """Summarize dominant learning style"""
        styles = {
            'visual': obj.visual_learner_score,
            'auditory': obj.auditory_learner_score,
            'kinesthetic': obj.kinesthetic_learner_score
        }
        dominant_style = max(styles, key=styles.get)
        return {
            'dominant': dominant_style,
            'scores': styles
        }

    def validate(self, attrs):
        """Ensure learning style scores are normalized"""
        scores = ['visual_learner_score', 'auditory_learner_score', 'kinesthetic_learner_score']
        total = sum(attrs.get(score, 0.5) for score in scores)
        if total > 0:
            for score in scores:
                if score in attrs:
                    attrs[score] = attrs[score] / total
        return attrs


class CulturalContextSerializer(serializers.Serializer):
    """
    Serializer for providing cultural context for a session
    """
    user_id = serializers.IntegerField()
    scenario_id = serializers.UUIDField(required=False)
    context_type = serializers.CharField(max_length=30, required=False)

    def validate(self, attrs):
        """Validate that either scenario_id or context_type is provided"""
        if not attrs.get('scenario_id') and not attrs.get('context_type'):
            raise serializers.ValidationError(
                "Either scenario_id or context_type must be provided"
            )
        return attrs


class CulturalFeedbackRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting culturally adapted feedback
    """
    feedback_type = serializers.ChoiceField(choices=[
        ('encouragement', 'Encouragement'),
        ('correction', 'Correction'),
        ('achievement', 'Achievement'),
        ('suggestion', 'Suggestion'),
        ('milestone', 'Milestone'),
    ])
    user_level = serializers.IntegerField(min_value=1)
    performance_score = serializers.FloatField(min_value=0, max_value=100)
    specific_error = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Additional validation for feedback requests"""
        if attrs['feedback_type'] == 'correction' and not attrs.get('specific_error'):
            raise serializers.ValidationError(
                "Specific error description is required for correction feedback"
            )
        return attrs
