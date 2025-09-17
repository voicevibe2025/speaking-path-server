from django.core.management.base import BaseCommand
from django.db import transaction
from apps.speaking_journey.models import Topic
from .topics import TOPICS

TOPICS = TOPICS


class Command(BaseCommand):
    help = 'Replaces all Speaking Journey topics with a fresh seed from the topics list.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Re-seeding Speaking Journey topics...'))

        # Delete all existing topics to ensure a clean slate
        self.stdout.write(self.style.WARNING('Deleting all existing topics...'))
        Topic.objects.all().delete()

        # Create new topics from the source list
        self.stdout.write('Creating new topics...')
        for idx, item in enumerate(TOPICS, start=1):
            title = item['title'].strip()
            Topic.objects.create(
                sequence=idx,
                title=title,
                description=item.get('description', ''),
                material_lines=item.get('material', []),
                conversation_example=item.get('conversation', []),
                vocabulary=item.get('vocabulary', []),
                fluency_practice_prompt=item.get('fluency_practice_prompt', []),
                is_active=True,
            )
            self.stdout.write(f" - CREATED: {idx}. {title}")

        total = Topic.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {total} topics.'))
