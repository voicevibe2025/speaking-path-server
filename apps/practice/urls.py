from django.urls import path
from .views import (
    RandomPromptView,
    PromptsByCategoryView,
    PromptDetailView,
    PromptListView,
    SubmitRecordingView,
    SessionDetailView,
    SessionEvaluationView,
)

app_name = 'practice'

urlpatterns = [
    path('prompts/random', RandomPromptView.as_view(), name='prompt_random'),
    path('prompts/category/<str:category>', PromptsByCategoryView.as_view(), name='prompts_by_category'),
    path('prompts/<uuid:id>', PromptDetailView.as_view(), name='prompt_detail'),
    path('prompts', PromptListView.as_view(), name='prompt_list'),

    path('sessions/submit/<uuid:prompt_id>', SubmitRecordingView.as_view(), name='submit_recording'),
    path('sessions/<uuid:session_id>', SessionDetailView.as_view(), name='session_detail'),
    path('sessions/<uuid:session_id>/evaluation', SessionEvaluationView.as_view(), name='session_evaluation'),
]
