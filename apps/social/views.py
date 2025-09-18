from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db import transaction

from apps.users.models import UserFollow
from .models import Post, PostLike, PostComment, PostCommentLike
from .serializers import PostSerializer, CreatePostRequest, CommentSerializer, CreateCommentRequest


def are_friends(user_a, user_b) -> bool:
    if user_a == user_b:
        return True
    try:
        return (
            UserFollow.objects.filter(follower=user_a, following=user_b).exists() and
            UserFollow.objects.filter(follower=user_b, following=user_a).exists()
        )
    except Exception:
        return False


class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.select_related('user').all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Support exactly one-of: text, image, link_url
        image = request.FILES.get('image')
        text = request.data.get('text', '')
        link_url = request.data.get('link_url', '')
        present = sum([1 if image else 0, 1 if (text or '').strip() else 0, 1 if (link_url or '').strip() else 0])
        if present != 1:
            return Response({'detail': 'Exactly one of text, image, or link_url must be provided.'}, status=status.HTTP_400_BAD_REQUEST)

        post = Post(user=request.user)
        if image:
            post.image = image
        elif (text or '').strip():
            post.text = (text or '').strip()
        else:
            # link
            if not (link_url.startswith('http://') or link_url.startswith('https://')):
                return Response({'detail': 'link_url must start with http:// or https://'}, status=status.HTTP_400_BAD_REQUEST)
            post.link_url = link_url.strip()
        post.save()

        serializer = self.get_serializer(post)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class PostLikeView(generics.GenericAPIView):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id)
        if not are_friends(request.user, post.user):
            return Response({'detail': 'Only friends can like.'}, status=status.HTTP_403_FORBIDDEN)
        # idempotent like
        PostLike.objects.get_or_create(post=post, user=request.user)
        return Response({'status': 'liked'})

    def delete(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id)
        if not are_friends(request.user, post.user):
            return Response({'detail': 'Only friends can unlike.'}, status=status.HTTP_403_FORBIDDEN)
        PostLike.objects.filter(post=post, user=request.user).delete()
        return Response({'status': 'unliked'})


class PostCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        # Newest first
        return PostComment.objects.select_related('user', 'post').filter(post_id=post_id).order_by('-created_at')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def list(self, request, *args, **kwargs):
        # Simplify: return list without pagination for now
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        if not are_friends(request.user, post.user):
            return Response({'detail': 'Only friends can comment.'}, status=status.HTTP_403_FORBIDDEN)
        req = CreateCommentRequest(data=request.data)
        req.is_valid(raise_exception=True)
        parent_id = req.validated_data.get('parent')
        parent = None
        if parent_id is not None:
            parent = get_object_or_404(PostComment, id=parent_id)
            if parent.post_id != post.id:
                return Response({'detail': 'Parent comment does not belong to this post.'}, status=status.HTTP_400_BAD_REQUEST)
        comment = PostComment.objects.create(post=post, user=request.user, text=req.validated_data['text'], parent=parent)
        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostCommentLikeView(generics.GenericAPIView):
    queryset = PostComment.objects.all()
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id: int):
        comment = get_object_or_404(PostComment, id=comment_id)
        if not are_friends(request.user, comment.post.user):
            return Response({'detail': 'Only friends can like.'}, status=status.HTTP_403_FORBIDDEN)
        PostCommentLike.objects.get_or_create(comment=comment, user=request.user)
        return Response({'status': 'liked'})

    def delete(self, request, comment_id: int):
        comment = get_object_or_404(PostComment, id=comment_id)
        if not are_friends(request.user, comment.post.user):
            return Response({'detail': 'Only friends can unlike.'}, status=status.HTTP_403_FORBIDDEN)
        PostCommentLike.objects.filter(comment=comment, user=request.user).delete()
        return Response({'status': 'unliked'})
