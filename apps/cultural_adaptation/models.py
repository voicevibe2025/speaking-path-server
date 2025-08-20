"""
Models for Cultural Adaptation app - Indonesian context personalization
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class CulturalProfile(models.Model):
    """
    User's cultural profile based on Hofstede's dimensions for Indonesia
    """
    REGION_CHOICES = [
        ('jakarta', 'DKI Jakarta'),
        ('west_java', 'Jawa Barat'),
        ('central_java', 'Jawa Tengah'),
        ('east_java', 'Jawa Timur'),
        ('bali', 'Bali'),
        ('sumatra', 'Sumatra'),
        ('kalimantan', 'Kalimantan'),
        ('sulawesi', 'Sulawesi'),
        ('papua', 'Papua'),
        ('other', 'Other'),
    ]

    EDUCATION_LEVEL_CHOICES = [
        ('sd', 'SD (Elementary)'),
        ('smp', 'SMP (Junior High)'),
        ('sma', 'SMA (Senior High)'),
        ('d3', 'D3 (Diploma)'),
        ('s1', 'S1 (Bachelor)'),
        ('s2', 'S2 (Master)'),
        ('s3', 'S3 (Doctorate)'),
    ]

    PROFESSION_CATEGORY_CHOICES = [
        ('student', 'Student'),
        ('professional', 'Professional'),
        ('business', 'Business Owner'),
        ('government', 'Government Employee'),
        ('healthcare', 'Healthcare Worker'),
        ('education', 'Educator'),
        ('creative', 'Creative Industry'),
        ('technology', 'Technology'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cultural_profile')

    # Demographics
    region = models.CharField(max_length=20, choices=REGION_CHOICES)
    urban_rural = models.CharField(max_length=10, choices=[('urban', 'Urban'), ('rural', 'Rural')])
    age_group = models.CharField(max_length=10, choices=[
        ('teen', '13-17'),
        ('young', '18-25'),
        ('adult', '26-35'),
        ('middle', '36-50'),
        ('senior', '50+')
    ])
    education_level = models.CharField(max_length=10, choices=EDUCATION_LEVEL_CHOICES)
    profession_category = models.CharField(max_length=20, choices=PROFESSION_CATEGORY_CHOICES, null=True, blank=True)

    # Hofstede's Cultural Dimensions (calibrated for Indonesia)
    power_distance_index = models.IntegerField(
        default=78,  # Indonesia's PDI
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    individualism_index = models.IntegerField(
        default=14,  # Indonesia's IDV (collectivist)
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    masculinity_index = models.IntegerField(
        default=46,  # Indonesia's MAS
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    uncertainty_avoidance_index = models.IntegerField(
        default=48,  # Indonesia's UAI
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    long_term_orientation_index = models.IntegerField(
        default=62,  # Indonesia's LTO
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    indulgence_index = models.IntegerField(
        default=38,  # Indonesia's IVR (restraint)
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Language preferences
    primary_language = models.CharField(max_length=50, default='Bahasa Indonesia')
    regional_language = models.CharField(max_length=50, null=True, blank=True)
    english_exposure_level = models.CharField(max_length=20, choices=[
        ('none', 'No exposure'),
        ('minimal', 'Minimal exposure'),
        ('moderate', 'Moderate exposure'),
        ('frequent', 'Frequent exposure'),
        ('daily', 'Daily exposure')
    ], default='minimal')

    # Learning preferences influenced by culture
    prefers_group_learning = models.BooleanField(default=True)  # Collectivist preference
    prefers_hierarchical_structure = models.BooleanField(default=True)  # High PDI
    needs_face_saving_feedback = models.BooleanField(default=True)  # Cultural sensitivity
    values_relationship_building = models.BooleanField(default=True)  # Collectivist

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cultural_profiles'
        verbose_name = 'Cultural Profile'
        verbose_name_plural = 'Cultural Profiles'

    def __str__(self):
        return f"{self.user.email} - {self.region}"


class CulturalScenario(models.Model):
    """
    Culturally relevant speaking scenarios for practice
    """
    CONTEXT_CHOICES = [
        ('formal_business', 'Formal Business'),
        ('casual_social', 'Casual Social'),
        ('education', 'Educational'),
        ('family', 'Family/Relative'),
        ('marketplace', 'Traditional Market'),
        ('religious', 'Religious Context'),
        ('government', 'Government Office'),
        ('healthcare', 'Healthcare'),
        ('tourism', 'Tourism'),
        ('technology', 'Technology'),
    ]

    FORMALITY_LEVEL_CHOICES = [
        ('very_formal', 'Very Formal'),
        ('formal', 'Formal'),
        ('neutral', 'Neutral'),
        ('informal', 'Informal'),
        ('very_informal', 'Very Informal'),
    ]

    scenario_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200)
    title_indonesian = models.CharField(max_length=200)
    description = models.TextField()
    description_indonesian = models.TextField()

    # Context
    context_type = models.CharField(max_length=30, choices=CONTEXT_CHOICES)
    formality_level = models.CharField(max_length=20, choices=FORMALITY_LEVEL_CHOICES)

    # Cultural elements
    involves_hierarchy = models.BooleanField(default=False)
    involves_face_saving = models.BooleanField(default=False)
    involves_indirect_communication = models.BooleanField(default=False)
    involves_group_harmony = models.BooleanField(default=False)

    # Regional relevance
    relevant_regions = models.JSONField(default=list, blank=True)  # List of region codes

    # Example dialogues
    example_phrases = models.JSONField(default=list)  # List of example English phrases
    cultural_notes = models.JSONField(default=dict)  # Cultural tips and notes

    # Difficulty
    difficulty_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    # Media
    image_url = models.URLField(null=True, blank=True)
    audio_example_url = models.URLField(null=True, blank=True)

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cultural_scenarios'
        verbose_name = 'Cultural Scenario'
        verbose_name_plural = 'Cultural Scenarios'
        ordering = ['difficulty_level', 'context_type']

    def __str__(self):
        return f"{self.title} ({self.context_type})"


class CulturalFeedbackTemplate(models.Model):
    """
    Culturally appropriate feedback templates
    """
    FEEDBACK_TYPE_CHOICES = [
        ('encouragement', 'Encouragement'),
        ('correction', 'Correction'),
        ('achievement', 'Achievement'),
        ('suggestion', 'Suggestion'),
        ('milestone', 'Milestone'),
    ]

    template_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)

    # Templates with cultural sensitivity
    template_english = models.TextField()
    template_indonesian = models.TextField()
    template_mixed = models.TextField(help_text="Mixed language template")

    # Cultural considerations
    uses_indirect_language = models.BooleanField(default=True)
    includes_encouragement = models.BooleanField(default=True)
    avoids_direct_criticism = models.BooleanField(default=True)

    # Contextual applicability
    min_level = models.IntegerField(default=1)
    max_level = models.IntegerField(default=100)

    # Regional variations
    regional_variations = models.JSONField(default=dict, blank=True)

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cultural_feedback_templates'
        verbose_name = 'Cultural Feedback Template'
        verbose_name_plural = 'Cultural Feedback Templates'

    def __str__(self):
        return f"{self.feedback_type} - Level {self.min_level}-{self.max_level}"


class IndonesianEnglishMapping(models.Model):
    """
    Common Indonesian-English language interference patterns
    """
    INTERFERENCE_TYPE_CHOICES = [
        ('pronunciation', 'Pronunciation'),
        ('grammar', 'Grammar'),
        ('vocabulary', 'Vocabulary'),
        ('idiom', 'Idiom'),
        ('pragmatic', 'Pragmatic'),
    ]

    mapping_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Pattern identification
    indonesian_pattern = models.CharField(max_length=200)
    english_equivalent = models.CharField(max_length=200)
    interference_type = models.CharField(max_length=20, choices=INTERFERENCE_TYPE_CHOICES)

    # Examples
    common_error = models.TextField()
    correct_form = models.TextField()
    explanation = models.TextField()
    explanation_indonesian = models.TextField()

    # Difficulty and frequency
    difficulty_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    frequency_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )

    # Teaching tips
    teaching_tips = models.JSONField(default=list)
    practice_exercises = models.JSONField(default=list)

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'indonesian_english_mappings'
        verbose_name = 'Indonesian-English Mapping'
        verbose_name_plural = 'Indonesian-English Mappings'
        ordering = ['-frequency_score', 'difficulty_level']

    def __str__(self):
        return f"{self.indonesian_pattern} → {self.english_equivalent}"


class CulturalAdaptationPreference(models.Model):
    """
    User preferences for cultural adaptation features
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cultural_preferences')

    # Content preferences
    prefers_bilingual_instructions = models.BooleanField(default=True)
    prefers_local_examples = models.BooleanField(default=True)
    prefers_religious_neutral_content = models.BooleanField(default=False)

    # Feedback preferences
    feedback_language = models.CharField(
        max_length=20,
        choices=[
            ('english', 'English Only'),
            ('indonesian', 'Indonesian Only'),
            ('mixed', 'Mixed'),
            ('adaptive', 'Adaptive')
        ],
        default='mixed'
    )
    feedback_formality = models.CharField(
        max_length=20,
        choices=[
            ('formal', 'Formal'),
            ('neutral', 'Neutral'),
            ('casual', 'Casual')
        ],
        default='neutral'
    )

    # Gamification preferences
    prefers_individual_achievements = models.BooleanField(default=False)
    prefers_group_achievements = models.BooleanField(default=True)
    prefers_competition = models.BooleanField(default=False)
    prefers_collaboration = models.BooleanField(default=True)

    # Learning style preferences
    visual_learner_score = models.FloatField(default=0.5, validators=[MinValueValidator(0), MaxValueValidator(1)])
    auditory_learner_score = models.FloatField(default=0.5, validators=[MinValueValidator(0), MaxValueValidator(1)])
    kinesthetic_learner_score = models.FloatField(default=0.5, validators=[MinValueValidator(0), MaxValueValidator(1)])

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cultural_adaptation_preferences'
        verbose_name = 'Cultural Adaptation Preference'
        verbose_name_plural = 'Cultural Adaptation Preferences'

    def __str__(self):
        return f"{self.user.email} preferences"
