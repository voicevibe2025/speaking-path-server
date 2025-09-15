from django.core.management.base import BaseCommand
from django.db import transaction
from apps.speaking_journey.models import Topic
from .topics import TOPICS

TOPICS = TOPICS


class Command(BaseCommand):
    help = 'Seeds Speaking Journey topics with material, description, and conversation. Idempotent and ordered.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete all existing topics before seeding')

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding Speaking Journey topics...'))

        if options['reset']:
            self.stdout.write(self.style.WARNING('Deleting all existing topics...'))
            Topic.objects.all().delete()

        seen_titles = set()
        for idx, item in enumerate(TOPICS, start=1):
            title = item['title'].strip()
            seen_titles.add(title)
            defaults = {
                'description': item.get('description', ''),
                'material_lines': item.get('material', []),
                'conversation_example': item.get('conversation', []),
                'vocabulary': item.get('vocabulary', []),
                'fluency_practice_prompt': item.get('fluency_practice_prompt', []),
                'sequence': idx,
                'is_active': True,
            }
            topic, created = Topic.objects.update_or_create(
                title=title,
                defaults=defaults
            )
            # Ensure unique sequence ordering if sequence changed
            if topic.sequence != idx:
                topic.sequence = idx
                topic.save(update_fields=['sequence'])

            action = 'CREATED' if created else 'UPDATED'
            self.stdout.write(f" - {action}: {idx}. {title} ({len(defaults['material_lines'])} lines)")

        total = Topic.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Done. Total topics: {total}'))
