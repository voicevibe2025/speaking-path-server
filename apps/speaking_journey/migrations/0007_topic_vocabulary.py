# Generated manually: Add vocabulary JSONField to Topic
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speaking_journey', '0006_topicprogress_fluency_completed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='vocabulary',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
