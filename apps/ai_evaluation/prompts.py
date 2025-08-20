"""
LLM Prompt Templates for AI Evaluation
Specialized prompts for Indonesian English learners
"""
from typing import Dict, Optional


class PromptTemplates:
    """
    Centralized prompt templates for LLM evaluation
    """

    @staticmethod
    def get_comprehensive_evaluation_prompt(
        transcription: str,
        scenario: str,
        user_level: str,
        cultural_context: str = "Indonesian"
    ) -> str:
        """
        Get comprehensive evaluation prompt
        """
        return f"""
        You are an expert English language teacher specializing in helping {cultural_context} learners.
        
        Analyze this transcribed speech from a {user_level} level student:
        
        TRANSCRIPTION: {transcription}
        SCENARIO: {scenario}
        
        Provide a comprehensive evaluation in JSON format with the following structure:
        {{
            "pronunciation": {{
                "score": [0-100],
                "common_errors": ["list of errors specific to {cultural_context} speakers"],
                "suggestions": ["actionable improvements"],
                "phonetic_focus": ["specific sounds to practice"]
            }},
            "grammar": {{
                "score": [0-100],
                "errors": [
                    {{
                        "text": "error text",
                        "correction": "corrected text",
                        "type": "error type",
                        "explanation": "why this is wrong"
                    }}
                ],
                "pattern_issues": ["recurring grammar patterns to work on"]
            }},
            "fluency": {{
                "score": [0-100],
                "pace": "too slow/good/too fast",
                "hesitations": "none/minimal/moderate/frequent",
                "filler_words": ["list of filler words used"],
                "flow": "natural/choppy/hesitant"
            }},
            "vocabulary": {{
                "score": [0-100],
                "level": "A1/A2/B1/B2/C1/C2",
                "range": "limited/moderate/good/excellent",
                "appropriateness": "suitable/partially suitable/unsuitable",
                "suggestions": ["words or phrases to learn"]
            }},
            "cultural_appropriateness": {{
                "score": [0-100],
                "formality": "too casual/appropriate/too formal",
                "politeness": "needs improvement/good/excellent",
                "cultural_notes": ["specific cultural observations"]
            }}
        }}
        
        Consider {cultural_context} learners' typical challenges:
        - Pronunciation of 'th', 'v', and consonant clusters
        - Article usage (a/an/the)
        - Present perfect vs simple past confusion
        - Formal/informal register awareness
        """

    @staticmethod
    def get_phonetic_analysis_prompt(
        transcription: str,
        user_level: str,
        focus_sounds: Optional[list] = None
    ) -> str:
        """
        Get prompt for detailed phonetic analysis
        """
        focus = ", ".join(focus_sounds) if focus_sounds else "all sounds"

        return f"""
        As a phonetics expert for Indonesian English learners, analyze the pronunciation in:
        
        TEXT: {transcription}
        LEVEL: {user_level}
        FOCUS: {focus}
        
        Provide detailed phonetic feedback:
        1. Identify mispronounced phonemes (use IPA notation)
        2. Note stress pattern errors
        3. Analyze intonation patterns
        4. Identify rhythm and timing issues
        5. Suggest minimal pairs for practice
        
        Common Indonesian speaker challenges to check:
        - /θ/ and /ð/ (th sounds) often replaced with /t/ and /d/
        - /v/ often replaced with /f/ or /p/
        - Final consonant clusters simplified
        - Vowel length distinctions missed
        - Word stress placement errors
        
        Format response as structured JSON.
        """

    @staticmethod
    def get_pragmatic_evaluation_prompt(
        transcription: str,
        scenario: str,
        relationship: str,
        cultural_context: str = "Indonesian"
    ) -> str:
        """
        Get prompt for pragmatic language evaluation
        """
        return f"""
        Evaluate the pragmatic appropriateness of this speech from a {cultural_context} speaker:
        
        SPEECH: {transcription}
        SCENARIO: {scenario}
        RELATIONSHIP: {relationship}
        
        Analyze based on:
        
        1. Speech Acts:
           - Are requests, apologies, compliments appropriate?
           - Is directness/indirectness suitable?
        
        2. Politeness Strategies:
           - Positive/negative face considerations
           - Power distance awareness
           - Collectivist vs individualist expressions
        
        3. Register and Formality:
           - Appropriate for the context?
           - Consistent throughout?
        
        4. Cultural Sensitivity:
           - Hofstede dimensions for {cultural_context}:
             * High power distance (78)
             * Collectivist society (14)
             * Moderate uncertainty avoidance (48)
           - Are these reflected appropriately?
        
        5. Conversational Conventions:
           - Turn-taking appropriateness
           - Topic management
           - Closing strategies
        
        Provide specific examples and culturally-sensitive suggestions.
        """

    @staticmethod
    def get_sequential_analysis_prompt(
        transcription: str,
        previous_context: Optional[str] = None
    ) -> str:
        """
        Get prompt for sequential/contextual analysis
        """
        context = previous_context or "No previous context"

        return f"""
        Analyze the sequential and contextual coherence of this speech:
        
        CURRENT: {transcription}
        PREVIOUS CONTEXT: {context}
        
        Evaluate:
        
        1. Discourse Coherence:
           - Logical flow of ideas
           - Use of discourse markers
           - Topic maintenance or shift
        
        2. Cohesion Devices:
           - Pronouns and reference
           - Conjunctions and transitions
           - Lexical cohesion
        
        3. Information Structure:
           - Given vs new information
           - Theme-rheme progression
           - Emphasis and focus
        
        4. Narrative/Argumentative Structure:
           - Clear introduction/body/conclusion?
           - Supporting details present?
           - Logical argumentation?
        
        5. Contextual Appropriateness:
           - Response relevance
           - Pragmatic coherence
           - Cultural context awareness
        
        Identify specific areas for improvement with examples.
        """

    @staticmethod
    def get_error_correction_prompt(
        transcription: str,
        error_type: str,
        user_level: str
    ) -> str:
        """
        Get prompt for specific error correction
        """
        return f"""
        As an error correction specialist for {user_level} level learners:
        
        TEXT: {transcription}
        ERROR TYPE: {error_type}
        
        Provide corrections focusing on {error_type}:
        
        1. Identify all {error_type} errors
        2. Provide the correction for each
        3. Explain WHY it's wrong (suitable for {user_level})
        4. Give a simple rule or pattern to remember
        5. Suggest practice exercises
        
        Use encouraging language and focus on progress, not perfection.
        
        Format as JSON with clear structure for each error.
        """

    @staticmethod
    def get_scenario_adaptation_prompt(
        base_scenario: str,
        user_level: str,
        cultural_background: str,
        interests: Optional[list] = None
    ) -> str:
        """
        Get prompt for adapting scenarios to user
        """
        interests_str = ", ".join(interests) if interests else "general topics"

        return f"""
        Adapt this speaking scenario for a {user_level} {cultural_background} learner:
        
        BASE SCENARIO: {base_scenario}
        INTERESTS: {interests_str}
        
        Create an adapted scenario that:
        
        1. Matches {user_level} language complexity
        2. Incorporates {cultural_background} cultural elements
        3. Relates to interests: {interests_str}
        4. Provides appropriate challenge without overwhelming
        5. Includes cultural bridge-building opportunities
        
        Structure the scenario with:
        - Clear context and roles
        - Specific communication goals
        - Key vocabulary/phrases to use
        - Cultural considerations
        - Success criteria
        
        Make it engaging and relevant to daily life or career goals.
        """

    @staticmethod
    def get_motivational_feedback_prompt(
        performance_data: Dict,
        user_goals: Optional[str] = None,
        learning_style: Optional[str] = None
    ) -> str:
        """
        Get prompt for generating motivational feedback
        """
        goals = user_goals or "improve English speaking"
        style = learning_style or "general"

        return f"""
        Generate motivational and constructive feedback for a learner:
        
        PERFORMANCE: {performance_data}
        GOALS: {goals}
        LEARNING STYLE: {style}
        
        Create feedback that:
        
        1. Celebrates Strengths:
           - Specific achievements
           - Progress from previous sessions
           - Effort recognition
        
        2. Frames Improvements Positively:
           - "Opportunities to grow"
           - "Next steps in your journey"
           - Concrete, achievable goals
        
        3. Provides Actionable Steps:
           - 3 specific things to practice
           - Resources or exercises
           - Time-bound mini-goals
        
        4. Cultural Sensitivity:
           - Group achievement emphasis (collectivist value)
           - Face-saving language
           - Respect for effort over outcome
        
        5. Personalization:
           - Reference their goals: {goals}
           - Match their learning style: {style}
           - Connect to real-world applications
        
        Keep tone encouraging, specific, and forward-looking.
        """

    @staticmethod
    def get_cultural_scenario_prompt(
        scenario_type: str,
        formality_level: str,
        cultural_elements: Optional[list] = None
    ) -> str:
        """
        Get prompt for creating culturally relevant scenarios
        """
        elements = ", ".join(cultural_elements) if cultural_elements else "Indonesian cultural context"

        return f"""
        Create a culturally-relevant English speaking scenario:
        
        TYPE: {scenario_type}
        FORMALITY: {formality_level}
        CULTURAL ELEMENTS: {elements}
        
        Design a scenario that:
        
        1. Authentic Context:
           - Realistic situation for Indonesian professionals/students
           - Incorporates {elements}
           - Balances local and international contexts
        
        2. Language Objectives:
           - Clear speaking goals
           - Target structures and vocabulary
           - Pragmatic competence focus
        
        3. Cultural Navigation:
           - Code-switching opportunities
           - Formal/informal register practice
           - Cross-cultural communication skills
        
        4. Engagement Factors:
           - Relevant to career/education goals
           - Problem-solving element
           - Social interaction component
        
        5. Difficulty Progression:
           - Entry point for various levels
           - Extension possibilities
           - Scaffolding suggestions
        
        Include:
        - Scenario description
        - Roles and relationships
        - Key phrases and vocabulary
        - Cultural tips
        - Evaluation criteria
        """
