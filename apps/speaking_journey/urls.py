from django.urls import path
from .views import SpeakingTopicsView, CompleteTopicView

app_name = 'speaking_journey'

urlpatterns = [
    path('topics', SpeakingTopicsView.as_view(), name='topics_list'),
    path('topics/<uuid:topic_id>/complete', CompleteTopicView.as_view(), name='topic_complete'),
]
