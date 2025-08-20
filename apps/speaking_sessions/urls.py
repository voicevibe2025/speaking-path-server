"""
URL patterns for speaking sessions
"""
from django.urls import path
from .views import (
    PracticeSessionListCreateView,
    PracticeSessionDetailView,
    SessionStatisticsView,
    AudioRecordingListView,
    SessionFeedbackListView,
    start_session,
    end_session
)

app_name = 'speaking_sessions'

urlpatterns = [
    # Session endpoints
    path('sessions/', PracticeSessionListCreateView.as_view(), name='session_list_create'),
    path('sessions/<uuid:session_id>/', PracticeSessionDetailView.as_view(), name='session_detail'),
    path('sessions/<uuid:session_id>/end/', end_session, name='end_session'),

    # Session related data
    path('sessions/<uuid:session_id>/recordings/', AudioRecordingListView.as_view(), name='session_recordings'),
    path('sessions/<uuid:session_id>/feedback/', SessionFeedbackListView.as_view(), name='session_feedback'),

    # Statistics
    path('statistics/', SessionStatisticsView.as_view(), name='statistics'),

    # Quick start endpoint
    path('start/', start_session, name='start_session'),
]
