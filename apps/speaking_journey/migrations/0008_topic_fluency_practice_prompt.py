# Generated manually: Add fluency_practice_prompt JSONField to Topic
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speaking_journey', '0007_topic_vocabulary'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='fluency_practice_prompt',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
