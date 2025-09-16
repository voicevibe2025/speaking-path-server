from django.urls import path
from .views import (
    SpeakingTopicsView,
    CompleteTopicView,
    SubmitPhraseRecordingView,
    UserPhraseRecordingsView,
    GenerateTTSView,
    SubmitFluencyPromptView,
    StartVocabularyPracticeView,
    SubmitVocabularyAnswerView,
    CompleteVocabularyPracticeView,
    SubmitConversationTurnView,
)

app_name = 'speaking_journey'

urlpatterns = [
    path('topics', SpeakingTopicsView.as_view(), name='topics'),
    path('topics/<uuid:topic_id>/complete', CompleteTopicView.as_view(), name='complete_topic'),
    path('topics/<uuid:topic_id>/phrases/submit', SubmitPhraseRecordingView.as_view(), name='submit_phrase'),
    path('topics/<uuid:topic_id>/conversation/submit', SubmitConversationTurnView.as_view(), name='submit_conversation_turn'),
    path('topics/<uuid:topic_id>/fluency/submit', SubmitFluencyPromptView.as_view(), name='submit_fluency_prompt'),
    # Vocabulary practice
    path('topics/<uuid:topic_id>/vocabulary/start', StartVocabularyPracticeView.as_view(), name='start_vocabulary'),
    path('topics/<uuid:topic_id>/vocabulary/answer', SubmitVocabularyAnswerView.as_view(), name='submit_vocabulary_answer'),
    path('topics/<uuid:topic_id>/vocabulary/complete', CompleteVocabularyPracticeView.as_view(), name='complete_vocabulary'),
    path('topics/<uuid:topic_id>/recordings', UserPhraseRecordingsView.as_view(), name='topic_recordings'),
    path('tts/generate', GenerateTTSView.as_view(), name='tts_generate'),
]
