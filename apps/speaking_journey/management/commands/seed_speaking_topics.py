from django.core.management.base import BaseCommand
from django.db import transaction
from apps.speaking_journey.models import Topic
from .topics import TOPICS

TOPICS = TOPICS


class Command(BaseCommand):
    help = 'Seeds Speaking Journey topics with material, description, and conversation. Idempotent and ordered.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Deactivate topics not present in TOPICS list')

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding Speaking Journey topics...'))

        seen_titles = set()
        for idx, item in enumerate(TOPICS, start=1):
            title = item['title'].strip()
            seen_titles.add(title)
            defaults = {
                'description': item.get('description', ''),
                'material_lines': item.get('material', []),
                'conversation_example': item.get('conversation', []),
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

        if options.get('reset'):
            deactivated = Topic.objects.exclude(title__in=seen_titles).update(is_active=False)
            if deactivated:
                self.stdout.write(self.style.WARNING(f'Deactivated {deactivated} topics not in TOPICS list'))

        total = Topic.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(f'Done. Active topics: {total}'))
