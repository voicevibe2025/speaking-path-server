# Generated migration for ChatModeUsage model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatModeUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usage_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('mode', models.CharField(choices=[('text', 'Text Chat'), ('voice', 'Voice Chat')], max_length=10)),
                ('session_id', models.UUIDField(default=uuid.uuid4)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('duration_seconds', models.IntegerField(default=0)),
                ('message_count', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('device_info', models.CharField(blank=True, max_length=100)),
                ('app_version', models.CharField(blank=True, max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_mode_usage', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Chat Mode Usage',
                'verbose_name_plural': 'Chat Mode Usages',
                'ordering': ['-started_at'],
            },
        ),
        migrations.AddIndex(
            model_name='chatmodeusage',
            index=models.Index(fields=['user', '-started_at'], name='analytics_c_user_id_5f8a9c_idx'),
        ),
        migrations.AddIndex(
            model_name='chatmodeusage',
            index=models.Index(fields=['mode', '-started_at'], name='analytics_c_mode_7d2b4e_idx'),
        ),
        migrations.AddIndex(
            model_name='chatmodeusage',
            index=models.Index(fields=['is_active'], name='analytics_c_is_acti_3c9f1a_idx'),
        ),
    ]
