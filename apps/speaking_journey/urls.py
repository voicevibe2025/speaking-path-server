from django.urls import path
from .views import (
    SpeakingTopicsView,
    CompleteTopicView,
    SubmitPhraseRecordingView,
    UserPhraseRecordingsView,
)

app_name = 'speaking_journey'

urlpatterns = [
    path('topics', SpeakingTopicsView.as_view(), name='topics'),
    path('topics/<uuid:topic_id>/complete', CompleteTopicView.as_view(), name='complete_topic'),
    path('topics/<uuid:topic_id>/phrases/submit', SubmitPhraseRecordingView.as_view(), name='submit_phrase'),
    path('topics/<uuid:topic_id>/recordings', UserPhraseRecordingsView.as_view(), name='topic_recordings'),
]
