from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.users.models import UserFollow, UserProfile
from .models import Post, PostLike, PostComment

User = get_user_model()


class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    displayName = serializers.SerializerMethodField()
    avatarUrl = serializers.SerializerMethodField()

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

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'text', 'imageUrl', 'linkUrl', 'createdAt', 'updatedAt',
            'likesCount', 'commentsCount', 'isLikedByMe', 'canInteract'
        ]
        read_only_fields = ['id', 'author', 'createdAt', 'updatedAt', 'likesCount', 'commentsCount', 'isLikedByMe', 'canInteract']

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
        if request.user == obj.user:
            return True
        # Mutual follow = friends
        return (
            UserFollow.objects.filter(follower=request.user, following=obj.user).exists() and
            UserFollow.objects.filter(follower=obj.user, following=request.user).exists()
        )

    def validate(self, attrs):
        request = self.context.get('request')
        # In create(), we might pass through; ensure one-of rule
        text = (request.data.get('text') if request else attrs.get('text')) or ''
        link_url = (request.data.get('link_url') if request else attrs.get('link_url')) or ''
        image = request.FILES.get('image') if request else None
        present = sum([1 if text.strip() else 0, 1 if link_url.strip() else 0, 1 if image else 0])
        if present != 1:
            raise serializers.ValidationError('Exactly one of text, image, or link_url must be provided.')
        # Optional: basic validation on link
        if link_url and not (link_url.startswith('http://') or link_url.startswith('https://')):
            raise serializers.ValidationError('link_url must start with http:// or https://')
        return attrs


class CreatePostRequest(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=True)
    link_url = serializers.URLField(required=False, allow_blank=True)


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at')

    class Meta:
        model = PostComment
        fields = ['id', 'post', 'author', 'text', 'createdAt']
        read_only_fields = ['id', 'post', 'author', 'createdAt']

    def get_author(self, obj: PostComment):
        return AuthorSerializer(obj.user, context=self.context).data


class CreateCommentRequest(serializers.Serializer):
    text = serializers.CharField(required=True, allow_blank=False)
