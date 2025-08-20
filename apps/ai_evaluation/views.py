"""
API Views for AI Evaluation
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import asyncio
import json
import logging

from .services import WhisperService, LLMEvaluationService
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transcribe_audio(request):
    """
    Transcribe audio using Whisper API

    Expected data:
    - audio_data: base64 encoded audio or file
    - language: target language (default: 'en')
    """
    try:
        audio_data = request.data.get('audio_data')
        language = request.data.get('language', 'en')

        if not audio_data:
            return Response(
                {'error': 'Audio data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize Whisper service
        whisper_service = WhisperService()

        # Run async transcription
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                whisper_service.transcribe_audio(audio_data, language)
            )
        finally:
            loop.close()

        return Response({
            'success': True,
            'transcription': result
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return Response(
            {'error': 'Transcription failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def evaluate_speech(request):
    """
    Comprehensive speech evaluation using LLM

    Expected data:
    - transcription: transcribed text
    - duration: speaking duration in seconds
    - scenario: practice scenario
    - user_level: user's proficiency level
    - context: optional conversation context
    """
    try:
        transcription = request.data.get('transcription')
        duration = request.data.get('duration', 0)
        scenario = request.data.get('scenario', 'General conversation')
        user_level = request.data.get('user_level', 'intermediate')
        context = request.data.get('context')

        if not transcription:
            return Response(
                {'error': 'Transcription is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize evaluation service
        eval_service = LLMEvaluationService()

        # Run async evaluations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run all evaluations in parallel
            pronunciation, grammar, fluency, vocabulary, cultural = loop.run_until_complete(
                asyncio.gather(
                    eval_service.evaluate_pronunciation(transcription, user_level=user_level),
                    eval_service.evaluate_grammar(transcription, context, user_level),
                    eval_service.evaluate_fluency(transcription, duration, user_level=user_level),
                    eval_service.evaluate_vocabulary(transcription, scenario, user_level),
                    eval_service.evaluate_cultural_appropriateness(transcription, scenario)
                )
            )

            # Generate comprehensive feedback
            feedback = loop.run_until_complete(
                eval_service.generate_comprehensive_feedback(
                    pronunciation, grammar, fluency, vocabulary, cultural
                )
            )
        finally:
            loop.close()

        return Response({
            'success': True,
            'evaluation': {
                'pronunciation': pronunciation,
                'grammar': grammar,
                'fluency': fluency,
                'vocabulary': vocabulary,
                'cultural': cultural,
                'comprehensive_feedback': feedback
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        return Response(
            {'error': 'Evaluation failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def evaluate_pronunciation(request):
    """
    Focused pronunciation evaluation

    Expected data:
    - transcription: transcribed text
    - audio_features: optional audio analysis features
    - user_level: user's proficiency level
    """
    try:
        transcription = request.data.get('transcription')
        audio_features = request.data.get('audio_features')
        user_level = request.data.get('user_level', 'intermediate')

        if not transcription:
            return Response(
                {'error': 'Transcription is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        eval_service = LLMEvaluationService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                eval_service.evaluate_pronunciation(
                    transcription, audio_features, user_level
                )
            )
        finally:
            loop.close()

        return Response({
            'success': True,
            'pronunciation_evaluation': result
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Pronunciation evaluation error: {str(e)}")
        return Response(
            {'error': 'Pronunciation evaluation failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def evaluate_grammar(request):
    """
    Focused grammar evaluation

    Expected data:
    - transcription: transcribed text
    - context: optional conversation context
    - user_level: user's proficiency level
    """
    try:
        transcription = request.data.get('transcription')
        context = request.data.get('context')
        user_level = request.data.get('user_level', 'intermediate')

        if not transcription:
            return Response(
                {'error': 'Transcription is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        eval_service = LLMEvaluationService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                eval_service.evaluate_grammar(transcription, context, user_level)
            )
        finally:
            loop.close()

        return Response({
            'success': True,
            'grammar_evaluation': result
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Grammar evaluation error: {str(e)}")
        return Response(
            {'error': 'Grammar evaluation failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_prompt(request):
    """
    Generate LLM prompt for custom evaluation

    Expected data:
    - prompt_type: type of prompt to generate
    - parameters: dict of parameters for the prompt
    """
    try:
        prompt_type = request.data.get('prompt_type')
        parameters = request.data.get('parameters', {})

        if not prompt_type:
            return Response(
                {'error': 'Prompt type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Map prompt types to methods
        prompt_methods = {
            'comprehensive': PromptTemplates.get_comprehensive_evaluation_prompt,
            'phonetic': PromptTemplates.get_phonetic_analysis_prompt,
            'pragmatic': PromptTemplates.get_pragmatic_evaluation_prompt,
            'sequential': PromptTemplates.get_sequential_analysis_prompt,
            'error_correction': PromptTemplates.get_error_correction_prompt,
            'scenario_adaptation': PromptTemplates.get_scenario_adaptation_prompt,
            'motivational': PromptTemplates.get_motivational_feedback_prompt,
            'cultural_scenario': PromptTemplates.get_cultural_scenario_prompt
        }

        if prompt_type not in prompt_methods:
            return Response(
                {'error': f'Invalid prompt type: {prompt_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate prompt
        prompt_method = prompt_methods[prompt_type]
        prompt = prompt_method(**parameters)

        return Response({
            'success': True,
            'prompt_type': prompt_type,
            'prompt': prompt
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Prompt generation error: {str(e)}")
        return Response(
            {'error': 'Prompt generation failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_session_progress(request):
    """
    Analyze progress across multiple sessions

    Expected data:
    - session_ids: list of session IDs to analyze
    - user_id: user ID
    """
    try:
        session_ids = request.data.get('session_ids', [])
        user_id = request.data.get('user_id')

        if not session_ids or not user_id:
            return Response(
                {'error': 'Session IDs and user ID are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Placeholder for progress analysis
        # In production, this would fetch session data and analyze trends
        progress_analysis = {
            'overall_improvement': 15.5,  # percentage
            'pronunciation_trend': 'improving',
            'grammar_trend': 'stable',
            'fluency_trend': 'improving',
            'vocabulary_trend': 'expanding',
            'strengths_developed': [
                'Better sentence structure',
                'Improved pronunciation of difficult sounds'
            ],
            'focus_areas': [
                'Article usage',
                'Present perfect tense'
            ],
            'milestones_reached': [
                'Completed 10 sessions',
                'Achieved B1 vocabulary level'
            ],
            'recommendations': [
                'Increase practice frequency to daily',
                'Focus on grammar exercises',
                'Try more challenging scenarios'
            ]
        }

        return Response({
            'success': True,
            'progress_analysis': progress_analysis
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Progress analysis error: {str(e)}")
        return Response(
            {'error': 'Progress analysis failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
