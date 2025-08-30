from django.core.management.base import BaseCommand
from django.db import transaction
from apps.speaking_journey.models import Topic


TOPICS = [
    {
        'title': 'Greetings and Introductions',
        'material': [
            'Hello! My name is [Your Name].',
            'Nice to meet you.',
            'How are you today?',
            "I am from Indonesia.",
            'I am learning English to improve my communication skills.'
        ]
    },
    {
        'title': 'Daily Activities',
        'material': [
            'I wake up at six in the morning.',
            'I go to work by bus.',
            'In the evening, I like to read books or watch movies.',
            'On weekends, I spend time with my family.'
        ]
    },
    {
        'title': 'Asking for Directions',
        'material': [
            'Excuse me, could you tell me how to get to the train station?',
            'Is it far from here?',
            'Should I turn left or right at the next intersection?',
            'Thank you for your help.'
        ]
    },
]


class Command(BaseCommand):
    help = 'Seeds Speaking Journey topics with material lines. Idempotent and ordered.'

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
                'material_lines': item.get('material', []),
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
