from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('speaking_journey', '0009_topicprogress_fluency_scores'),
        ('speaking_journey', '0009_topicprogress_pronunciation_total_score'),
    ]

    operations = [
        # Merge migration to resolve parallel 0009 migrations.
    ]
