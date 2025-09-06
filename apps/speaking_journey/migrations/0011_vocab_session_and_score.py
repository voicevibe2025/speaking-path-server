from django.db import migrations, models
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('speaking_journey', '0010_merge'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='topicprogress',
            name='vocabulary_total_score',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='VocabularyPracticeSession',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('session_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('questions', models.JSONField(default=list, blank=True)),
                ('total_questions', models.IntegerField(default=0)),
                ('current_index', models.IntegerField(default=0)),
                ('correct_count', models.IntegerField(default=0)),
                ('total_score', models.IntegerField(default=0)),
                ('completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='vocab_sessions', to=settings.AUTH_USER_MODEL)),
                ('topic', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='vocab_sessions', to='speaking_journey.topic')),
            ],
            options={
                'db_table': 'speaking_journey_vocab_sessions',
                'verbose_name': 'Vocabulary Practice Session',
                'verbose_name_plural': 'Vocabulary Practice Sessions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='vocabularypracticesession',
            index=models.Index(fields=['session_id'], name='sj_vocab_session_idx'),
        ),
        migrations.AddIndex(
            model_name='vocabularypracticesession',
            index=models.Index(fields=['user', 'topic'], name='sj_vocab_user_topic_idx'),
        ),
    ]
