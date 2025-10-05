"""
API Views for AI Evaluation
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import asyncio
import json
import logging

from google import genai
from google.genai import types as genai_types

from .services import WhisperService, LLMEvaluationService
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


def _ensure_live_connect_config(payload: dict) -> dict:
    response_modalities = payload.get('response_modalities')
    if not isinstance(response_modalities, list) or not response_modalities:
        response_modalities = ['TEXT']

    connect_config: dict[str, object] = {
        'response_modalities': response_modalities,
    }

    system_instruction = payload.get('system_instruction')
    if isinstance(system_instruction, str) and system_instruction.strip():
        connect_config['system_instruction'] = system_instruction.strip()

    output_audio_config = payload.get('output_audio_config')
    if isinstance(output_audio_config, dict):
        connect_config['output_audio_config'] = output_audio_config
    
    speech_config = payload.get('speech_config')
    if isinstance(speech_config, dict):
        connect_config['speech_config'] = speech_config

    proactivity_config = payload.get('proactivity_config')
    if isinstance(proactivity_config, dict):
        connect_config['proactivity_config'] = proactivity_config
    
    # Handle function declarations for tool use
    function_declarations = payload.get('function_declarations')
    if function_declarations:
        # If it's a JSON string, parse it
        if isinstance(function_declarations, str):
            try:
                function_declarations = json.loads(function_declarations)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse function_declarations JSON: {function_declarations[:100]}")
                function_declarations = None
        
        # If we have valid function declarations, add tools to config
        if function_declarations and isinstance(function_declarations, dict):
            func_decls = function_declarations.get('functionDeclarations', [])
            if func_decls:
                connect_config['tools'] = [{'function_declarations': func_decls}]
                logger.info(f"Added {len(func_decls)} function declarations to Live API config")

    return connect_config


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_live_session_token(request):
    """
    Issue a short-lived Gemini Live API token for direct client connections.

    Optional JSON body:
    - model: override Gemini model (default gemini-live-2.5-flash-preview)
    - response_modalities: list of response modalities (default ['TEXT'])
    - system_instruction: optional system prompt to lock into the session
    - lock_additional_fields: list of extra LiveConnectConfig fields to lock
    """

    if not settings.GEMINI_API_KEY:
        return Response(
            {
                'error': 'GEMINI_API_KEY is not configured on the server.',
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    payload = request.data if isinstance(request.data, dict) else {}

    model = payload.get('model') or 'gemini-live-2.5-flash-preview'
    connect_config = _ensure_live_connect_config(payload)

    lock_additional_fields = payload.get('lock_additional_fields')
    if not isinstance(lock_additional_fields, list):
        lock_additional_fields = []

    try:
        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options={'api_version': 'v1alpha'}
        )

        token_config = genai_types.CreateAuthTokenConfig(
            live_connect_constraints=genai_types.LiveConnectConstraints(
                model=model,
                config=genai_types.LiveConnectConfig(**connect_config),
            ),
            lock_additional_fields=lock_additional_fields,
        )

        auth_token = client.auth_tokens.create(config=token_config)

        token_value = (
            getattr(auth_token, 'token', None)
            or getattr(auth_token, 'auth_token', None)
            or getattr(auth_token, 'name', None)
        )

        expires_at = (
            getattr(auth_token, 'expire_time', None)
            or getattr(auth_token, 'expireTime', None)
        )

        if not token_value:
            raise ValueError('AuthToken missing token payload')

        response_payload = {
            'token': token_value,
            'expiresAt': expires_at,
            'sessionId': getattr(auth_token, 'session_id', None),
            'model': model,
            'responseModalities': connect_config.get('response_modalities'),
            'lockedFields': lock_additional_fields,
        }

        return Response(response_payload, status=status.HTTP_200_OK)

    except Exception as exc:  # pragma: no cover - defensive handling of SDK errors
        logger.exception('Failed to create Gemini Live auth token: %s', exc)
        return Response(
            {
                'error': 'Unable to create Gemini Live token.',
                'details': str(exc),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )


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
