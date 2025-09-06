from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speaking_journey', '0008_topic_fluency_practice_prompt'),
    ]

    operations = [
        migrations.AddField(
            model_name='topicprogress',
            name='pronunciation_total_score',
            field=models.IntegerField(default=0),
        ),
    ]
