from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    """
    A simple social Post that can include text and/or image, or a link (exclusive).
    Visible to all authenticated users. Likes/comments allowed for all authenticated users.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/', null=True, blank=True)
    link_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Post({self.id}) by {self.user_id}"


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('post', 'user')]
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Like({self.user_id} -> {self.post_id})"


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    text = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['post', 'parent', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Comment({self.id}) on Post({self.post_id}) by {self.user_id}"


class PostCommentLike(models.Model):
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('comment', 'user')]
        indexes = [
            models.Index(fields=['comment']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"CommentLike({self.user_id} -> {self.comment_id})"


class Notification(models.Model):
    """In-app notifications for social interactions."""
    TYPE_POST_LIKE = 'post_like'
    TYPE_POST_COMMENT = 'post_comment'
    TYPE_COMMENT_LIKE = 'comment_like'
    TYPE_COMMENT_REPLY = 'comment_reply'
    TYPE_USER_FOLLOW = 'user_follow'
    TYPE_REPORT_RESOLVED = 'report_resolved'
    TYPE_MODERATION_ACTION = 'moderation_action'

    NOTIF_TYPES = [
        (TYPE_POST_LIKE, 'Post liked'),
        (TYPE_POST_COMMENT, 'New comment on your post'),
        (TYPE_COMMENT_LIKE, 'Comment liked'),
        (TYPE_COMMENT_REPLY, 'New reply to your comment'),
        (TYPE_USER_FOLLOW, 'New follower'),
        (TYPE_REPORT_RESOLVED, 'Report resolved'),
        (TYPE_MODERATION_ACTION, 'Moderation action applied'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actor_notifications')
    type = models.CharField(max_length=32, choices=NOTIF_TYPES)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications')
    comment = models.ForeignKey(PostComment, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['recipient', 'read_at']),
            models.Index(fields=['type', 'created_at']),
        ]

    def __str__(self):
        return f"Notification({self.type}) to {self.recipient_id} on Post({self.post_id})"
