from django.urls import path
from .views import (
    SpeakingTopicsView,
    CompleteTopicView,
    SubmitPhraseRecordingView,
    UserPhraseRecordingsView,
    GenerateTTSView,
    SubmitFluencyPromptView,
    SubmitFluencyRecordingView,
    StartVocabularyPracticeView,
    SubmitVocabularyAnswerView,
    CompleteVocabularyPracticeView,
    StartListeningPracticeView,
    SubmitListeningAnswerView,
    CompleteListeningPracticeView,
    SubmitConversationTurnView,
    SpeakingActivitiesView,
    DebugTopicStatusView,
    SeedPerfectScoresView,
    RecomputeTopicAggregatesView,
    CoachAnalysisView,
    CoachAnalysisRefreshView,
    LingoLeagueView,
)

app_name = 'speaking_journey'

urlpatterns = [
    path('topics', SpeakingTopicsView.as_view(), name='topics'),
    path('topics/<uuid:topic_id>/complete', CompleteTopicView.as_view(), name='complete_topic'),
    path('topics/<uuid:topic_id>/phrases/submit', SubmitPhraseRecordingView.as_view(), name='submit_phrase'),
    path('topics/<uuid:topic_id>/conversation/submit', SubmitConversationTurnView.as_view(), name='submit_conversation_turn'),
    path('topics/<uuid:topic_id>/fluency/submit', SubmitFluencyPromptView.as_view(), name='submit_fluency_prompt'),
    path('topics/<uuid:topic_id>/fluency/submit-recording', SubmitFluencyRecordingView.as_view(), name='submit_fluency_recording'),
    # Vocabulary practice
    path('topics/<uuid:topic_id>/vocabulary/start', StartVocabularyPracticeView.as_view(), name='start_vocabulary'),
    path('topics/<uuid:topic_id>/vocabulary/answer', SubmitVocabularyAnswerView.as_view(), name='submit_vocabulary_answer'),
    path('topics/<uuid:topic_id>/vocabulary/complete', CompleteVocabularyPracticeView.as_view(), name='complete_vocabulary'),
    # Listening practice
    path('topics/<uuid:topic_id>/listening/start', StartListeningPracticeView.as_view(), name='start_listening'),
    path('topics/<uuid:topic_id>/listening/answer', SubmitListeningAnswerView.as_view(), name='submit_listening_answer'),
    path('topics/<uuid:topic_id>/listening/complete', CompleteListeningPracticeView.as_view(), name='complete_listening'),
    path('topics/<uuid:topic_id>/recordings', UserPhraseRecordingsView.as_view(), name='topic_recordings'),
    path('activities', SpeakingActivitiesView.as_view(), name='activities'),
    path('lingo-league', LingoLeagueView.as_view(), name='lingo_league'),
    path('tts/generate', GenerateTTSView.as_view(), name='tts_generate'),
    # AI Coach
    path('coach/analysis', CoachAnalysisView.as_view(), name='coach_analysis'),
    path('coach/analysis/refresh', CoachAnalysisRefreshView.as_view(), name='coach_analysis_refresh'),
    # Debug endpoints
    path('topics/<uuid:topic_id>/debug', DebugTopicStatusView.as_view(), name='debug_topic_status'),
    path('topics/<uuid:topic_id>/seed-perfect', SeedPerfectScoresView.as_view(), name='seed_perfect_scores'),
    path('topics/<uuid:topic_id>/recompute', RecomputeTopicAggregatesView.as_view(), name='recompute_topic_aggregates'),
]
