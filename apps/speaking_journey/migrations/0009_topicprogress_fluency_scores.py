# Generated manually: Add fluency scoring fields to TopicProgress
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speaking_journey', '0008_topic_fluency_practice_prompt'),
    ]

    operations = [
        migrations.AddField(
            model_name='topicprogress',
            name='fluency_total_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='topicprogress',
            name='fluency_prompt_scores',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
