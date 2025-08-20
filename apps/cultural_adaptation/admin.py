"""
Admin configuration for Cultural Adaptation app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CulturalProfile,
    CulturalScenario,
    CulturalFeedbackTemplate,
    IndonesianEnglishMapping,
    CulturalAdaptationPreference
)


@admin.register(CulturalProfile)
class CulturalProfileAdmin(admin.ModelAdmin):
    """Admin interface for Cultural Profiles"""
    list_display = [
        'user_email', 'region_display', 'urban_rural', 'age_group',
        'education_display', 'english_exposure', 'cultural_indices_summary',
        'created_at'
    ]
    list_filter = [
        'region', 'urban_rural', 'age_group', 'education_level',
        'english_exposure_level', 'profession_category'
    ]
    search_fields = ['user__email', 'user__username', 'regional_language']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Demographics', {
            'fields': (
                'region', 'urban_rural', 'age_group',
                'education_level', 'profession_category'
            )
        }),
        ('Hofstede Cultural Dimensions', {
            'fields': (
                'power_distance_index', 'individualism_index',
                'masculinity_index', 'uncertainty_avoidance_index',
                'long_term_orientation_index', 'indulgence_index'
            ),
            'description': 'Cultural dimension indices (0-100) calibrated for Indonesia'
        }),
        ('Language Preferences', {
            'fields': (
                'primary_language', 'regional_language',
                'english_exposure_level'
            )
        }),
        ('Learning Preferences', {
            'fields': (
                'prefers_group_learning', 'prefers_hierarchical_structure',
                'needs_face_saving_feedback', 'values_relationship_building'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        })
    )

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def region_display(self, obj):
        """Display region with color coding"""
        colors = {
            'jakarta': '#FF6B6B',
            'bali': '#4ECDC4',
            'west_java': '#45B7D1',
            'central_java': '#96CEB4',
            'east_java': '#FFEAA7',
            'sumatra': '#DDA0DD',
            'kalimantan': '#98D8C8',
            'sulawesi': '#F7DC6F',
            'papua': '#F8B739',
            'other': '#BDC3C7'
        }
        color = colors.get(obj.region, '#BDC3C7')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_region_display()
        )
    region_display.short_description = 'Region'
    region_display.admin_order_field = 'region'

    def education_display(self, obj):
        """Display education level"""
        return obj.get_education_level_display()
    education_display.short_description = 'Education'
    education_display.admin_order_field = 'education_level'

    def english_exposure(self, obj):
        """Display English exposure with color"""
        exposure_colors = {
            'none': '#E74C3C',
            'minimal': '#E67E22',
            'moderate': '#F39C12',
            'frequent': '#52C41A',
            'daily': '#27AE60'
        }
        color = exposure_colors.get(obj.english_exposure_level, '#95A5A6')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_english_exposure_level_display()
        )
    english_exposure.short_description = 'English Exposure'
    english_exposure.admin_order_field = 'english_exposure_level'

    def cultural_indices_summary(self, obj):
        """Display summary of cultural indices"""
        return format_html(
            'PDI:{} IDV:{} MAS:{} UAI:{}',
            obj.power_distance_index,
            obj.individualism_index,
            obj.masculinity_index,
            obj.uncertainty_avoidance_index
        )
    cultural_indices_summary.short_description = 'Cultural Indices'


@admin.register(CulturalScenario)
class CulturalScenarioAdmin(admin.ModelAdmin):
    """Admin interface for Cultural Scenarios"""
    list_display = [
        'title', 'context_type_display', 'formality_display',
        'difficulty_display', 'cultural_elements', 'is_active',
        'created_at'
    ]
    list_filter = [
        'context_type', 'formality_level', 'difficulty_level',
        'is_active', 'involves_hierarchy', 'involves_face_saving'
    ]
    search_fields = ['title', 'title_indonesian', 'description']
    readonly_fields = ['scenario_id', 'created_at', 'updated_at']
    list_editable = ['is_active']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'scenario_id', 'title', 'title_indonesian',
                'description', 'description_indonesian'
            )
        }),
        ('Context Settings', {
            'fields': (
                'context_type', 'formality_level', 'difficulty_level'
            )
        }),
        ('Cultural Elements', {
            'fields': (
                'involves_hierarchy', 'involves_face_saving',
                'involves_indirect_communication', 'involves_group_harmony'
            )
        }),
        ('Regional & Examples', {
            'fields': (
                'relevant_regions', 'example_phrases', 'cultural_notes'
            )
        }),
        ('Media', {
            'fields': ('image_url', 'audio_example_url')
        }),
        ('Status & Metadata', {
            'fields': ('is_active', 'created_at', 'updated_at')
        })
    )

    def context_type_display(self, obj):
        """Display context type with icon"""
        icons = {
            'formal_business': '💼',
            'casual_social': '👥',
            'education': '🎓',
            'family': '👨‍👩‍👧‍👦',
            'marketplace': '🛒',
            'religious': '🕌',
            'government': '🏛️',
            'healthcare': '🏥',
            'tourism': '✈️',
            'technology': '💻'
        }
        icon = icons.get(obj.context_type, '📝')
        return format_html(
            '{} {}',
            icon, obj.get_context_type_display()
        )
    context_type_display.short_description = 'Context'
    context_type_display.admin_order_field = 'context_type'

    def formality_display(self, obj):
        """Display formality level with color"""
        colors = {
            'very_formal': '#2C3E50',
            'formal': '#34495E',
            'neutral': '#7F8C8D',
            'informal': '#95A5A6',
            'very_informal': '#BDC3C7'
        }
        color = colors.get(obj.formality_level, '#95A5A6')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_formality_level_display()
        )
    formality_display.short_description = 'Formality'
    formality_display.admin_order_field = 'formality_level'

    def difficulty_display(self, obj):
        """Display difficulty with stars"""
        stars = '⭐' * obj.difficulty_level
        return format_html('{} ({})', stars, obj.difficulty_level)
    difficulty_display.short_description = 'Difficulty'
    difficulty_display.admin_order_field = 'difficulty_level'

    def cultural_elements(self, obj):
        """Display active cultural elements"""
        elements = []
        if obj.involves_hierarchy:
            elements.append('Hierarchy')
        if obj.involves_face_saving:
            elements.append('Face-saving')
        if obj.involves_indirect_communication:
            elements.append('Indirect')
        if obj.involves_group_harmony:
            elements.append('Harmony')
        return ', '.join(elements) if elements else 'None'
    cultural_elements.short_description = 'Cultural Elements'


@admin.register(CulturalFeedbackTemplate)
class CulturalFeedbackTemplateAdmin(admin.ModelAdmin):
    """Admin interface for Cultural Feedback Templates"""
    list_display = [
        'feedback_type_display', 'level_range', 'language_settings',
        'cultural_approach', 'is_active', 'created_at'
    ]
    list_filter = [
        'feedback_type', 'is_active', 'uses_indirect_language',
        'includes_encouragement', 'avoids_direct_criticism'
    ]
    search_fields = [
        'template_english', 'template_indonesian', 'template_mixed'
    ]
    readonly_fields = ['template_id', 'created_at']
    list_editable = ['is_active']

    fieldsets = (
        ('Basic Information', {
            'fields': ('template_id', 'feedback_type')
        }),
        ('Template Content', {
            'fields': (
                'template_english', 'template_indonesian', 'template_mixed'
            ),
            'description': 'Use {score}, {level}, {improvement} as placeholders'
        }),
        ('Cultural Considerations', {
            'fields': (
                'uses_indirect_language', 'includes_encouragement',
                'avoids_direct_criticism'
            )
        }),
        ('Applicability', {
            'fields': ('min_level', 'max_level', 'regional_variations')
        }),
        ('Status & Metadata', {
            'fields': ('is_active', 'created_at')
        })
    )

    def feedback_type_display(self, obj):
        """Display feedback type with emoji"""
        emojis = {
            'encouragement': '💪',
            'correction': '✏️',
            'achievement': '🏆',
            'suggestion': '💡',
            'milestone': '🎯'
        }
        emoji = emojis.get(obj.feedback_type, '📝')
        return format_html(
            '{} {}',
            emoji, obj.get_feedback_type_display()
        )
    feedback_type_display.short_description = 'Type'
    feedback_type_display.admin_order_field = 'feedback_type'

    def level_range(self, obj):
        """Display level range"""
        return format_html(
            'Level {}-{}',
            obj.min_level, obj.max_level
        )
    level_range.short_description = 'Level Range'

    def language_settings(self, obj):
        """Display available languages"""
        languages = []
        if obj.template_english:
            languages.append('EN')
        if obj.template_indonesian:
            languages.append('ID')
        if obj.template_mixed:
            languages.append('MIX')
        return ' | '.join(languages)
    language_settings.short_description = 'Languages'

    def cultural_approach(self, obj):
        """Display cultural approach indicators"""
        approaches = []
        if obj.uses_indirect_language:
            approaches.append('Indirect')
        if obj.includes_encouragement:
            approaches.append('Encouraging')
        if obj.avoids_direct_criticism:
            approaches.append('Non-critical')
        return ', '.join(approaches)
    cultural_approach.short_description = 'Approach'


@admin.register(IndonesianEnglishMapping)
class IndonesianEnglishMappingAdmin(admin.ModelAdmin):
    """Admin interface for Indonesian-English Mappings"""
    list_display = [
        'pattern_display', 'interference_type_display',
        'difficulty_display', 'frequency_display', 'is_active',
        'created_at'
    ]
    list_filter = [
        'interference_type', 'difficulty_level', 'is_active'
    ]
    search_fields = [
        'indonesian_pattern', 'english_equivalent',
        'common_error', 'correct_form'
    ]
    readonly_fields = ['mapping_id', 'created_at']
    list_editable = ['is_active']

    fieldsets = (
        ('Pattern Identification', {
            'fields': (
                'mapping_id', 'indonesian_pattern', 'english_equivalent',
                'interference_type'
            )
        }),
        ('Error & Correction', {
            'fields': (
                'common_error', 'correct_form',
                'explanation', 'explanation_indonesian'
            )
        }),
        ('Metrics', {
            'fields': ('difficulty_level', 'frequency_score')
        }),
        ('Teaching Resources', {
            'fields': ('teaching_tips', 'practice_exercises')
        }),
        ('Status & Metadata', {
            'fields': ('is_active', 'created_at')
        })
    )

    def pattern_display(self, obj):
        """Display pattern mapping"""
        return format_html(
            '{} → {}',
            obj.indonesian_pattern, obj.english_equivalent
        )
    pattern_display.short_description = 'Pattern'

    def interference_type_display(self, obj):
        """Display interference type with color"""
        colors = {
            'pronunciation': '#E74C3C',
            'grammar': '#3498DB',
            'vocabulary': '#2ECC71',
            'idiom': '#F39C12',
            'pragmatic': '#9B59B6'
        }
        color = colors.get(obj.interference_type, '#95A5A6')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_interference_type_display()
        )
    interference_type_display.short_description = 'Type'
    interference_type_display.admin_order_field = 'interference_type'

    def difficulty_display(self, obj):
        """Display difficulty with bars"""
        bars = '▮' * obj.difficulty_level + '▯' * (5 - obj.difficulty_level)
        return format_html('{} ({})', bars, obj.difficulty_level)
    difficulty_display.short_description = 'Difficulty'
    difficulty_display.admin_order_field = 'difficulty_level'

    def frequency_display(self, obj):
        """Display frequency as percentage"""
        percentage = obj.frequency_score * 100
        color = '#E74C3C' if percentage >= 70 else '#F39C12' if percentage >= 40 else '#2ECC71'
        return format_html(
            '<span style="color: {};">{:.0f}%</span>',
            color, percentage
        )
    frequency_display.short_description = 'Frequency'
    frequency_display.admin_order_field = 'frequency_score'


@admin.register(CulturalAdaptationPreference)
class CulturalAdaptationPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for Cultural Adaptation Preferences"""
    list_display = [
        'user_email', 'feedback_settings', 'content_preferences',
        'learning_style_display', 'collaboration_preference',
        'updated_at'
    ]
    list_filter = [
        'feedback_language', 'feedback_formality',
        'prefers_bilingual_instructions', 'prefers_collaboration'
    ]
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'learning_style_chart']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Content Preferences', {
            'fields': (
                'prefers_bilingual_instructions', 'prefers_local_examples',
                'prefers_religious_neutral_content'
            )
        }),
        ('Feedback Settings', {
            'fields': ('feedback_language', 'feedback_formality')
        }),
        ('Gamification Preferences', {
            'fields': (
                'prefers_individual_achievements', 'prefers_group_achievements',
                'prefers_competition', 'prefers_collaboration'
            )
        }),
        ('Learning Style', {
            'fields': (
                'visual_learner_score', 'auditory_learner_score',
                'kinesthetic_learner_score', 'learning_style_chart'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        })
    )

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def feedback_settings(self, obj):
        """Display feedback preferences"""
        return format_html(
            '{} / {}',
            obj.get_feedback_language_display(),
            obj.get_feedback_formality_display()
        )
    feedback_settings.short_description = 'Feedback'

    def content_preferences(self, obj):
        """Display content preferences"""
        prefs = []
        if obj.prefers_bilingual_instructions:
            prefs.append('Bilingual')
        if obj.prefers_local_examples:
            prefs.append('Local')
        if obj.prefers_religious_neutral_content:
            prefs.append('Neutral')
        return ', '.join(prefs) if prefs else 'None'
    content_preferences.short_description = 'Content'

    def learning_style_display(self, obj):
        """Display dominant learning style"""
        styles = {
            'Visual': obj.visual_learner_score,
            'Auditory': obj.auditory_learner_score,
            'Kinesthetic': obj.kinesthetic_learner_score
        }
        dominant = max(styles, key=styles.get)
        return format_html(
            '<strong>{}</strong> ({:.0f}%)',
            dominant, styles[dominant] * 100
        )
    learning_style_display.short_description = 'Learning Style'

    def collaboration_preference(self, obj):
        """Display collaboration vs competition preference"""
        if obj.prefers_collaboration and not obj.prefers_competition:
            return format_html('<span style="color: #2ECC71;">Collaborative</span>')
        elif obj.prefers_competition and not obj.prefers_collaboration:
            return format_html('<span style="color: #E74C3C;">Competitive</span>')
        else:
            return format_html('<span style="color: #F39C12;">Balanced</span>')
    collaboration_preference.short_description = 'Style'

    def learning_style_chart(self, obj):
        """Display learning style as a simple chart"""
        v_pct = int(obj.visual_learner_score * 100)
        a_pct = int(obj.auditory_learner_score * 100)
        k_pct = int(obj.kinesthetic_learner_score * 100)

        return format_html(
            '''
            <div style="font-family: monospace;">
                Visual:      [{}] {}%<br>
                Auditory:    [{}] {}%<br>
                Kinesthetic: [{}] {}%
            </div>
            ''',
            '█' * (v_pct // 10) + '░' * (10 - v_pct // 10), v_pct,
            '█' * (a_pct // 10) + '░' * (10 - a_pct // 10), a_pct,
            '█' * (k_pct // 10) + '░' * (10 - k_pct // 10), k_pct
        )
    learning_style_chart.short_description = 'Learning Style Distribution'
