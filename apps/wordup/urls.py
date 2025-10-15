from django.urls import path
from .views import (
    GetRandomWordView,
    EvaluateExampleView,
    MasteredWordsView,
    WordProgressStatsView,
    WordTTSView,
)

app_name = 'wordup'

urlpatterns = [
    path('random-word/', GetRandomWordView.as_view(), name='random-word'),
    path('evaluate/', EvaluateExampleView.as_view(), name='evaluate'),
    path('mastered-words/', MasteredWordsView.as_view(), name='mastered-words'),
    path('stats/', WordProgressStatsView.as_view(), name='stats'),
    path('tts/', WordTTSView.as_view(), name='tts'),
]
