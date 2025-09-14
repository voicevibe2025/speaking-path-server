"""
AI Evaluation Services for VoiceVibe
Handles Whisper API transcription and LLM-based evaluation
"""
import os
import json
import asyncio
import aiohttp
try:
    import openai  # Optional dependency; only used if OPENAI_API_KEY is set
except Exception:  # pragma: no cover - optional dependency not installed
    openai = None
from typing import Dict, List, Optional, Any
import base64
import tempfile
import whisper
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class WhisperService:
    """
    Service for handling Whisper API transcription
    """

    def __init__(self):
        # Keep API key detection for potential future hosted use, but local model doesn't need it
        self.api_key = os.getenv('WHISPER_API_KEY', os.getenv('OPENAI_API_KEY'))
        # Lazy-load local whisper model name (match existing implementation)
        self.model_name = "tiny.en"

    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe audio using Whisper API

        Args:
            audio_data: Audio file bytes
            language: Target language code

        Returns:
            Transcription result with text and metadata
        """
        try:
            # Accept base64 string or raw bytes
            if isinstance(audio_data, str):
                try:
                    audio_b64 = audio_data.split(",", 1)[-1]
                except Exception:
                    audio_b64 = audio_data
                audio_bytes = base64.b64decode(audio_b64)
            else:
                audio_bytes = audio_data

            # Persist to a temp file that Whisper (ffmpeg) can read
            with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                temp_path = tmp.name

            # Local OpenAI Whisper (tiny.en) just like SpeakingJourney
            try:
                if not hasattr(self, "_model") or self._model is None:
                    self._model = whisper.load_model(self.model_name)
                result = self._model.transcribe(temp_path, language=language)
                text = (result.get("text") or "").strip()
                out = {
                    "text": text,
                    "language": language,
                    "duration": 0,
                    "segments": []
                }
                logger.info("Audio transcribed successfully via local whisper (%s)", self.model_name)
                return out
            finally:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Whisper transcription error: {str(e)}")
            raise


class LLMEvaluationService:
    """
    Service for LLM-based language evaluation
    """

    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = "gpt-4"

        if self.openai_api_key and openai is not None:
            openai.api_key = self.openai_api_key
        elif self.openai_api_key and openai is None:
            logger.info("OpenAI SDK not installed; skipping OpenAI init")

    async def evaluate_pronunciation(
        self,
        transcription: str,
        audio_features: Optional[Dict] = None,
        user_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Evaluate pronunciation using LLM prompt engineering

        Args:
            transcription: Transcribed text
            audio_features: Optional audio analysis features
            user_level: User's proficiency level

        Returns:
            Pronunciation evaluation results
        """
        prompt = self._create_pronunciation_prompt(transcription, user_level)

        try:
            # Placeholder for LLM API call
            evaluation = {
                "score": 85,
                "issues": [],
                "suggestions": [
                    "Focus on vowel sounds in words like 'about'",
                    "Practice the 'th' sound in 'think' and 'that'"
                ],
                "phonetic_analysis": {
                    "stress_patterns": "Good",
                    "intonation": "Natural",
                    "rhythm": "Slightly rushed"
                }
            }

            return evaluation

        except Exception as e:
            logger.error(f"Pronunciation evaluation error: {str(e)}")
            raise

    async def evaluate_grammar(
        self,
        transcription: str,
        context: Optional[str] = None,
        user_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Evaluate grammar using LLM analysis

        Args:
            transcription: Transcribed text
            context: Conversation context
            user_level: User's proficiency level

        Returns:
            Grammar evaluation results
        """
        prompt = self._create_grammar_prompt(transcription, context, user_level)

        try:
            # Placeholder for LLM API call
            evaluation = {
                "score": 78,
                "errors": [
                    {
                        "type": "verb_tense",
                        "text": "I go there yesterday",
                        "correction": "I went there yesterday",
                        "explanation": "Use past tense 'went' for past actions"
                    }
                ],
                "suggestions": [
                    "Review past tense verb forms",
                    "Practice subject-verb agreement"
                ],
                "complexity_level": "intermediate"
            }

            return evaluation

        except Exception as e:
            logger.error(f"Grammar evaluation error: {str(e)}")
            raise

    async def evaluate_fluency(
        self,
        transcription: str,
        duration: float,
        pauses: Optional[List[float]] = None,
        user_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Evaluate speaking fluency

        Args:
            transcription: Transcribed text
            duration: Total speaking duration
            pauses: List of pause durations
            user_level: User's proficiency level

        Returns:
            Fluency evaluation results
        """
        words_per_minute = self._calculate_wpm(transcription, duration)

        try:
            evaluation = {
                "score": 82,
                "words_per_minute": words_per_minute,
                "pace": "good",
                "hesitations": "minimal",
                "filler_words": ["um", "uh"],
                "suggestions": [
                    "Try to reduce filler words",
                    "Maintain consistent speaking pace"
                ]
            }

            return evaluation

        except Exception as e:
            logger.error(f"Fluency evaluation error: {str(e)}")
            raise

    async def evaluate_vocabulary(
        self,
        transcription: str,
        topic: Optional[str] = None,
        user_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Evaluate vocabulary usage

        Args:
            transcription: Transcribed text
            topic: Conversation topic
            user_level: User's proficiency level

        Returns:
            Vocabulary evaluation results
        """
        prompt = self._create_vocabulary_prompt(transcription, topic, user_level)

        try:
            evaluation = {
                "score": 75,
                "level": "B1",
                "word_variety": "moderate",
                "advanced_words": ["accomplish", "perspective"],
                "suggestions": [
                    "Use more varied adjectives",
                    "Try incorporating phrasal verbs"
                ],
                "topic_relevance": "good"
            }

            return evaluation

        except Exception as e:
            logger.error(f"Vocabulary evaluation error: {str(e)}")
            raise

    async def evaluate_cultural_appropriateness(
        self,
        transcription: str,
        scenario: str,
        cultural_context: str = "Indonesian"
    ) -> Dict[str, Any]:
        """
        Evaluate cultural appropriateness for Indonesian learners

        Args:
            transcription: Transcribed text
            scenario: Speaking scenario
            cultural_context: Cultural background

        Returns:
            Cultural appropriateness evaluation
        """
        prompt = self._create_cultural_prompt(transcription, scenario, cultural_context)

        try:
            evaluation = {
                "score": 88,
                "appropriateness": "good",
                "formality_level": "appropriate",
                "cultural_notes": [
                    "Good use of polite expressions",
                    "Consider adding more formal greetings in business contexts"
                ],
                "hofstede_alignment": {
                    "power_distance": "respected",
                    "collectivism": "demonstrated",
                    "uncertainty_avoidance": "acknowledged"
                }
            }

            return evaluation

        except Exception as e:
            logger.error(f"Cultural evaluation error: {str(e)}")
            raise

    async def generate_comprehensive_feedback(
        self,
        pronunciation: Dict,
        grammar: Dict,
        fluency: Dict,
        vocabulary: Dict,
        cultural: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive feedback based on all evaluations

        Returns:
            Comprehensive feedback with scores and recommendations
        """
        # Calculate overall score
        scores = [
            pronunciation.get('score', 0),
            grammar.get('score', 0),
            fluency.get('score', 0),
            vocabulary.get('score', 0)
        ]
        if cultural:
            scores.append(cultural.get('score', 0))

        overall_score = sum(scores) / len(scores)

        # Compile feedback
        feedback = {
            "overall_score": round(overall_score, 1),
            "pronunciation_score": pronunciation.get('score', 0),
            "grammar_score": grammar.get('score', 0),
            "fluency_score": fluency.get('score', 0),
            "vocabulary_score": vocabulary.get('score', 0),
            "strengths": self._identify_strengths(scores),
            "areas_for_improvement": self._identify_improvements(
                pronunciation, grammar, fluency, vocabulary
            ),
            "personalized_recommendations": self._generate_recommendations(
                pronunciation, grammar, fluency, vocabulary, user_preferences
            ),
            "next_practice_focus": self._suggest_next_focus(scores),
            "motivational_message": self._generate_motivation(overall_score)
        }

        if cultural:
            feedback["cultural_score"] = cultural.get('score', 0)
            feedback["cultural_insights"] = cultural.get('cultural_notes', [])

        return feedback

    # Helper methods for prompt creation
    def _create_pronunciation_prompt(self, text: str, level: str) -> str:
        return f"""
        Analyze the pronunciation challenges in this transcribed speech from an {level} English learner:
        
        Text: {text}
        
        Identify:
        1. Likely pronunciation errors for Indonesian speakers
        2. Stress pattern issues
        3. Intonation problems
        4. Specific phonemes that need practice
        
        Provide constructive feedback suitable for {level} level.
        """

    def _create_grammar_prompt(self, text: str, context: Optional[str], level: str) -> str:
        return f"""
        Analyze the grammar in this transcribed speech from an {level} English learner:
        
        Text: {text}
        Context: {context or 'General conversation'}
        
        Identify:
        1. Grammar errors with corrections
        2. Sentence structure issues
        3. Tense consistency problems
        4. Subject-verb agreement errors
        
        Provide explanations suitable for {level} level Indonesian learners.
        """

    def _create_vocabulary_prompt(self, text: str, topic: Optional[str], level: str) -> str:
        return f"""
        Analyze the vocabulary usage in this transcribed speech from an {level} English learner:
        
        Text: {text}
        Topic: {topic or 'General'}
        
        Evaluate:
        1. Vocabulary range and variety
        2. Word choice appropriateness
        3. Use of collocations and phrases
        4. Academic or professional vocabulary if relevant
        
        Suggest improvements for {level} level.
        """

    def _create_cultural_prompt(self, text: str, scenario: str, cultural_context: str) -> str:
        return f"""
        Analyze the cultural appropriateness of this speech from an {cultural_context} speaker:
        
        Text: {text}
        Scenario: {scenario}
        
        Consider:
        1. Formality level appropriateness
        2. Politeness strategies
        3. Cultural sensitivity
        4. Hofstede's cultural dimensions for {cultural_context}
        
        Provide culturally-aware feedback.
        """

    def _calculate_wpm(self, text: str, duration: float) -> int:
        """Calculate words per minute"""
        if duration <= 0:
            return 0
        word_count = len(text.split())
        return int((word_count / duration) * 60)

    def _identify_strengths(self, scores: List[float]) -> List[str]:
        """Identify user's strengths based on scores"""
        strengths = []
        categories = ["Pronunciation", "Grammar", "Fluency", "Vocabulary"]

        for i, score in enumerate(scores[:4]):
            if score >= 80:
                strengths.append(f"Strong {categories[i].lower()}")

        return strengths if strengths else ["Consistent effort across all areas"]

    def _identify_improvements(self, *evaluations) -> List[str]:
        """Identify areas needing improvement"""
        improvements = []

        for eval_data in evaluations:
            if eval_data.get('score', 100) < 70:
                if 'suggestions' in eval_data:
                    improvements.extend(eval_data['suggestions'][:1])

        return improvements[:3] if improvements else ["Continue practicing regularly"]

    def _generate_recommendations(self, *evaluations, user_preferences=None) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []

        # Add specific recommendations based on lowest scores
        for eval_data in evaluations:
            if eval_data and eval_data.get('suggestions'):
                recommendations.extend(eval_data['suggestions'][:1])

        # Add preference-based recommendations
        if user_preferences:
            if user_preferences.get('immediate_correction'):
                recommendations.append("Practice with immediate error correction exercises")
            if user_preferences.get('visual_learning'):
                recommendations.append("Use visual aids and diagrams for grammar patterns")

        return recommendations[:5]

    def _suggest_next_focus(self, scores: List[float]) -> str:
        """Suggest next area to focus on"""
        categories = ["pronunciation", "grammar", "fluency", "vocabulary"]
        min_score_idx = scores[:4].index(min(scores[:4]))
        return f"Focus on improving {categories[min_score_idx]} in your next session"

    def _generate_motivation(self, score: float) -> str:
        """Generate motivational message based on score"""
        if score >= 85:
            return "Excellent work! You're making great progress!"
        elif score >= 70:
            return "Good job! Keep practicing to reach the next level!"
        elif score >= 55:
            return "You're improving! Stay consistent with your practice."
        else:
            return "Keep going! Every practice session brings you closer to your goals."
