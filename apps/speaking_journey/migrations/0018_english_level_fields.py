from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speaking_journey', '0017_coachanalysiscache'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='difficulty',
            field=models.CharField(
                choices=[('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('ADVANCED', 'Advanced')],
                default='INTERMEDIATE',
                max_length=12,
                db_index=True,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='english_level',
            field=models.CharField(
                choices=[('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('ADVANCED', 'Advanced')],
                max_length=12,
                null=True,
                blank=True,
            ),
        ),
    ]
