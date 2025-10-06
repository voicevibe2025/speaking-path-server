from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Post, PostLike, PostComment, PostCommentLike, Notification
from apps.users.models import PrivacySettings

User = get_user_model()


class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    displayName = serializers.SerializerMethodField()
    avatarUrl = serializers.SerializerMethodField()
    isOnline = serializers.SerializerMethodField()

    def get_displayName(self, obj):
        try:
            profile = obj.profile  # UserProfile one-to-one
            first = getattr(obj, 'first_name', '') or ''
            last = getattr(obj, 'last_name', '') or ''
            full = (first + ' ' + last).strip()
            return full or (obj.username or 'User')
        except Exception:
            return obj.username or 'User'

    def get_avatarUrl(self, obj):
        request = self.context.get('request')
        try:
            profile = obj.profile  # type: ignore[attr-defined]
            if profile.avatar and hasattr(profile.avatar, 'url'):
                return request.build_absolute_uri(profile.avatar.url) if request else profile.avatar.url
            return profile.avatar_url or None
        except Exception:
            return None

    def get_isOnline(self, obj):
        """
        Compute whether the user is online (last activity within 5 minutes).
        Respects privacy settings.
        """
        request = self.context.get('request')
        
        # If viewing own profile, always show true online status
        try:
            if request and request.user.is_authenticated and request.user == obj:
                if obj.last_activity:
                    now = timezone.now()
                    threshold = now - timedelta(minutes=5)
                    return obj.last_activity >= threshold
                return False
        except Exception:
            pass
        
        # Check privacy settings
        try:
            privacy_settings = PrivacySettings.objects.filter(user=obj).first()
            if privacy_settings and privacy_settings.hide_online_status:
                return False
        except Exception:
            pass
        
        # Return online status
        try:
            if obj.last_activity:
                now = timezone.now()
                threshold = now - timedelta(minutes=5)
                return obj.last_activity >= threshold
        except Exception:
            pass
        
        return False


class PostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    imageUrl = serializers.SerializerMethodField()
    linkUrl = serializers.CharField(source='link_url', required=False, allow_blank=True)
    createdAt = serializers.DateTimeField(source='created_at')
    updatedAt = serializers.DateTimeField(source='updated_at')
    likesCount = serializers.SerializerMethodField()
    commentsCount = serializers.SerializerMethodField()
    isLikedByMe = serializers.SerializerMethodField()
    canInteract = serializers.SerializerMethodField()
    canDelete = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'text', 'imageUrl', 'linkUrl', 'createdAt', 'updatedAt',
            'likesCount', 'commentsCount', 'isLikedByMe', 'canInteract', 'canDelete'
        ]
        read_only_fields = ['id', 'author', 'createdAt', 'updatedAt', 'likesCount', 'commentsCount', 'isLikedByMe', 'canInteract', 'canDelete']

    def get_author(self, obj: Post):
        return AuthorSerializer(obj.user, context=self.context).data

    def get_imageUrl(self, obj: Post):
        request = self.context.get('request')
        try:
            if obj.image and hasattr(obj.image, 'url'):
                return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        except Exception:
            pass
        return None

    def get_likesCount(self, obj: Post):
        return obj.likes.count()

    def get_commentsCount(self, obj: Post):
        return obj.comments.count()

    def get_isLikedByMe(self, obj: Post):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return PostLike.objects.filter(post=obj, user=request.user).exists()

    def get_canInteract(self, obj: Post):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        # Any authenticated user can interact (like/comment)
        return True

    def get_canDelete(self, obj: Post):
        request = self.context.get('request')
        try:
            return bool(request and request.user.is_authenticated and (request.user == obj.user or request.user.is_staff))
        except Exception:
            return False

    def validate(self, attrs):
        request = self.context.get('request')
        # Allow text and/or image. If link_url is provided, it must be exclusive.
        text = ((request.data.get('text') if request else attrs.get('text')) or '').strip()
        link_url = ((request.data.get('link_url') if request else attrs.get('link_url')) or '').strip()
        image = request.FILES.get('image') if request else None

        if link_url:
            if image or text:
                raise serializers.ValidationError('link_url cannot be combined with text or image.')
            if not (link_url.startswith('http://') or link_url.startswith('https://')):
                raise serializers.ValidationError('link_url must start with http:// or https://')
        else:
            if not (text or image):
                raise serializers.ValidationError('Provide text and/or image.')
        return attrs


class CreatePostRequest(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=True)
    link_url = serializers.URLField(required=False, allow_blank=True)


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at')
    parent = serializers.IntegerField(source='parent_id', required=False, allow_null=True)
    likesCount = serializers.SerializerMethodField()
    isLikedByMe = serializers.SerializerMethodField()
    canDelete = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ['id', 'post', 'author', 'text', 'parent', 'createdAt', 'likesCount', 'isLikedByMe', 'canDelete']
        read_only_fields = ['id', 'post', 'author', 'createdAt', 'likesCount', 'isLikedByMe', 'canDelete']

    def get_author(self, obj: PostComment):
        return AuthorSerializer(obj.user, context=self.context).data

    def get_likesCount(self, obj: PostComment):
        return obj.likes.count()

    def get_isLikedByMe(self, obj: PostComment):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return PostCommentLike.objects.filter(comment=obj, user=request.user).exists()

    def get_canDelete(self, obj: PostComment):
        request = self.context.get('request')
        try:
            if not request or not request.user.is_authenticated:
                return False
            # Comment author or the post author (moderation) or staff
            return bool(request.user == obj.user or request.user == obj.post.user or request.user.is_staff)
        except Exception:
            return False


class CreateCommentRequest(serializers.Serializer):
    text = serializers.CharField(required=True, allow_blank=False)
    parent = serializers.IntegerField(required=False, allow_null=True)


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    postId = serializers.IntegerField(source='post_id', required=False, allow_null=True)
    commentId = serializers.IntegerField(source='comment_id', required=False, allow_null=True)
    createdAt = serializers.DateTimeField(source='created_at')
    read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'type', 'actor', 'postId', 'commentId', 'createdAt', 'read']
        read_only_fields = ['id', 'type', 'actor', 'postId', 'commentId', 'createdAt', 'read']

    def get_actor(self, obj: Notification):
        return AuthorSerializer(obj.actor, context=self.context).data

    def get_read(self, obj: Notification):
        return obj.read_at is not None
