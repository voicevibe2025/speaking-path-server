from django.urls import path
from .views import PostListCreateView, PostLikeView, PostCommentListCreateView, PostCommentLikeView, PostDetailView, PostCommentDetailView

urlpatterns = [
    path('posts/', PostListCreateView.as_view(), name='post-list-create'),
    path('posts/<int:post_id>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:post_id>/like/', PostLikeView.as_view(), name='post-like'),
    path('posts/<int:post_id>/comments/', PostCommentListCreateView.as_view(), name='post-comments'),
    path('comments/<int:comment_id>/like/', PostCommentLikeView.as_view(), name='comment-like'),
    path('comments/<int:comment_id>/', PostCommentDetailView.as_view(), name='comment-detail'),
]
