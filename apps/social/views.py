from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from .models import Post, PostLike, PostComment, PostCommentLike, Notification
from apps.users.models import UserBlock
from .serializers import PostSerializer, CreatePostRequest, CommentSerializer, CreateCommentRequest, NotificationSerializer


class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.select_related('user').all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Post.objects.select_related('user').all()
        user = self.request.user
        # Exclude posts by users the requester has blocked or who have blocked the requester
        qs = qs.exclude(user__blocked_by_relations__blocker=user) \
               .exclude(user__blocking_relations__blocked_user=user)
        return qs

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
        # Allow text and/or image, or link_url (link cannot be combined with others)
        image = request.FILES.get('image')
        text = (request.data.get('text') or '').strip()
        link_url = (request.data.get('link_url') or '').strip()

        if link_url:
            # Link posts are exclusive (no text/image combination for now)
            if image or text:
                return Response({'detail': 'link_url cannot be combined with text or image.'}, status=status.HTTP_400_BAD_REQUEST)
            if not (link_url.startswith('http://') or link_url.startswith('https://')):
                return Response({'detail': 'link_url must start with http:// or https://'}, status=status.HTTP_400_BAD_REQUEST)
            post = Post(user=request.user, link_url=link_url)
            post.save()
        else:
            if not image and not text:
                return Response({'detail': 'Provide text and/or image.'}, status=status.HTTP_400_BAD_REQUEST)
            post = Post(user=request.user)
            if image:
                post.image = image
            if text:
                post.text = text
            post.save()

        serializer = self.get_serializer(post)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class PostLikeView(generics.GenericAPIView):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id)
        # Block enforcement
        if UserBlock.objects.filter(blocker=request.user, blocked_user=post.user).exists() or \
           UserBlock.objects.filter(blocker=post.user, blocked_user=request.user).exists():
            raise PermissionDenied("You cannot like content from this user.")
        # idempotent like
        like, created = PostLike.objects.get_or_create(post=post, user=request.user)
        # Emit notification only when a new like is created and not self-like
        if created and post.user_id != request.user.id:
            Notification.objects.create(
                recipient=post.user,
                actor=request.user,
                type=Notification.TYPE_POST_LIKE,
                post=post,
                comment=None,
            )
        return Response({'status': 'liked'})

    def delete(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id)
        # Allow unliking without block checks to let users clean up state
        PostLike.objects.filter(post=post, user=request.user).delete()
        return Response({'status': 'unliked'})


class PostDetailView(generics.GenericAPIView):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id)
        # Block enforcement: deny viewing posts when a block exists either way
        if UserBlock.objects.filter(blocker=request.user, blocked_user=post.user).exists() or \
           UserBlock.objects.filter(blocker=post.user, blocked_user=request.user).exists():
            raise PermissionDenied("You cannot view this post.")
        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id)
        # Only author or staff can delete
        if not (request.user == post.user or request.user.is_staff):
            return Response({'detail': 'Not allowed to delete this post.'}, status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        # Block enforcement: deny listing comments for blocked relationships
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        if UserBlock.objects.filter(blocker=request.user, blocked_user=post.user).exists() or \
           UserBlock.objects.filter(blocker=post.user, blocked_user=request.user).exists():
            raise PermissionDenied("You cannot view comments for this post.")

        # Simplify: return list without pagination for now
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        # Block enforcement: deny commenting with blocked user
        if UserBlock.objects.filter(blocker=request.user, blocked_user=post.user).exists() or \
           UserBlock.objects.filter(blocker=post.user, blocked_user=request.user).exists():
            raise PermissionDenied("You cannot comment on this user's post.")
        req = CreateCommentRequest(data=request.data)
        req.is_valid(raise_exception=True)
        parent_id = req.validated_data.get('parent')
        parent = None
        if parent_id is not None:
            parent = get_object_or_404(PostComment, id=parent_id)
            if parent.post_id != post.id:
                return Response({'detail': 'Parent comment does not belong to this post.'}, status=status.HTTP_400_BAD_REQUEST)
        comment = PostComment.objects.create(post=post, user=request.user, text=req.validated_data['text'], parent=parent)
        # Emit notification
        if parent is not None:
            # Reply to a comment -> notify comment author (avoid self-notif)
            if parent.user_id != request.user.id:
                Notification.objects.create(
                    recipient=parent.user,
                    actor=request.user,
                    type=Notification.TYPE_COMMENT_REPLY,
                    post=post,
                    comment=comment,
                )
        else:
            # New top-level comment -> notify post author (avoid self-notif)
            if post.user_id != request.user.id:
                Notification.objects.create(
                    recipient=post.user,
                    actor=request.user,
                    type=Notification.TYPE_POST_COMMENT,
                    post=post,
                    comment=comment,
                )
        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostCommentLikeView(generics.GenericAPIView):
    queryset = PostComment.objects.all()
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id: int):
        comment = get_object_or_404(PostComment, id=comment_id)
        # Block enforcement
        if UserBlock.objects.filter(blocker=request.user, blocked_user=comment.user).exists() or \
           UserBlock.objects.filter(blocker=comment.user, blocked_user=request.user).exists():
            raise PermissionDenied("You cannot like this comment.")
        like, created = PostCommentLike.objects.get_or_create(comment=comment, user=request.user)
        # Notify comment author on new like (avoid self-notif)
        if created and comment.user_id != request.user.id:
            Notification.objects.create(
                recipient=comment.user,
                actor=request.user,
                type=Notification.TYPE_COMMENT_LIKE,
                post=comment.post,
                comment=comment,
            )
        return Response({'status': 'liked'})

    def delete(self, request, comment_id: int):
        comment = get_object_or_404(PostComment, id=comment_id)
        # Allow unliking without block checks
        PostCommentLike.objects.filter(comment=comment, user=request.user).delete()
        return Response({'status': 'unliked'})


class PostCommentDetailView(generics.GenericAPIView):
    queryset = PostComment.objects.all()
    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id: int):
        comment = get_object_or_404(PostComment, id=comment_id)
        # Allow deletion by comment author, post author, or staff
        if not (request.user == comment.user or request.user == comment.post.user or request.user.is_staff):
            return Response({'detail': 'Not allowed to delete this comment.'}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Notification.objects.select_related('actor', 'recipient', 'post').filter(recipient=self.request.user)
        unread = self.request.query_params.get('unread')
        if unread in ('1', 'true', 'True'):
            qs = qs.filter(read_at__isnull=True)
        limit = self.request.query_params.get('limit')
        try:
            if limit:
                return qs.order_by('-created_at')[: int(limit)]
        except Exception:
            pass
        return qs.order_by('-created_at')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class NotificationMarkReadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notif_id: int):
        notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
        if notif.read_at is None:
            notif.read_at = timezone.now()
            notif.save(update_fields=['read_at'])
        return Response({'status': 'ok'})


class NotificationMarkAllReadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(read_at=timezone.now())
        return Response({'status': 'ok'})


class NotificationUnreadCountView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()
        return Response({'count': count})
