"""
URL patterns for AI evaluation
"""
from django.urls import path
from .views import (
    create_live_session_token,
    transcribe_audio,
    evaluate_speech,
    evaluate_pronunciation,
    evaluate_grammar,
    generate_prompt,
    analyze_session_progress
)

app_name = 'ai_evaluation'

urlpatterns = [
    # Gemini Live session token
    path('live/token/', create_live_session_token, name='create_live_session_token'),

    # Transcription
    path('transcribe/', transcribe_audio, name='transcribe_audio'),

    # Comprehensive evaluation
    path('evaluate/', evaluate_speech, name='evaluate_speech'),

    # Focused evaluations
    path('evaluate/pronunciation/', evaluate_pronunciation, name='evaluate_pronunciation'),
    path('evaluate/grammar/', evaluate_grammar, name='evaluate_grammar'),

    # Prompt generation
    path('prompt/generate/', generate_prompt, name='generate_prompt'),

    # Progress analysis
    path('progress/analyze/', analyze_session_progress, name='analyze_progress'),
]
