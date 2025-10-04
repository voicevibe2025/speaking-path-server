# Generated migration for follow notifications

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0003_notification'),
    ]

    operations = [
        # Update notification type choices to include user_follow
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(
                choices=[
                    ('post_like', 'Post liked'),
                    ('post_comment', 'New comment on your post'),
                    ('comment_like', 'Comment liked'),
                    ('comment_reply', 'New reply to your comment'),
                    ('user_follow', 'New follower'),
                ],
                max_length=32
            ),
        ),
        # Make post field nullable to support follow notifications
        migrations.AlterField(
            model_name='notification',
            name='post',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notifications',
                to='social.post'
            ),
        ),
    ]
