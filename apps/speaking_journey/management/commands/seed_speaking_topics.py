from django.core.management.base import BaseCommand
from django.db import transaction
from apps.speaking_journey.models import Topic


TOPICS = [
    {
        'title': 'Greetings and Introductions',
        'description': 'Learn common phrases for greeting people and introducing yourself in everyday situations such as meeting new classmates or colleagues.',
        'material': [
            'Hello! My name is [Your Name].',
            'Nice to meet you.',
            'How are you today?',
            'I am from Indonesia.',
            'I am learning English to improve my communication skills.'
        ],
        'conversation': [
            {'speaker': 'A', 'text': 'Hi! I\'m Alex. Nice to meet you.'},
            {'speaker': 'B', 'text': 'Nice to meet you too, Alex. I\'m Maya.'},
            {'speaker': 'A', 'text': 'How are you today?'},
            {'speaker': 'B', 'text': 'I\'m good, thank you. And you?'},
            {'speaker': 'A', 'text': 'Doing well, thanks!'}
        ]
    },
    {
        'title': 'Daily Activities',
        'description': 'Talk about your daily routine, including mornings, commute, work or school, and evening activities.',
        'material': [
            'I wake up at six in the morning.',
            'I go to work by bus.',
            'In the evening, I like to read books or watch movies.',
            'On weekends, I spend time with my family.'
        ],
        'conversation': [
            {'speaker': 'A', 'text': 'What time do you usually get up?'},
            {'speaker': 'B', 'text': 'Around six. I make breakfast and then catch the bus.'},
            {'speaker': 'A', 'text': 'Do you have time to exercise?'},
            {'speaker': 'B', 'text': 'Yes, I go for a short walk in the evening.'}
        ]
    },
    {
        'title': 'Asking for Directions',
        'description': 'Politely ask for and follow directions in public places like streets, stations, or malls.',
        'material': [
            'Excuse me, could you tell me how to get to the train station?',
            'Is it far from here?',
            'Should I turn left or right at the next intersection?',
            'Thank you for your help.'
        ],
        'conversation': [
            {'speaker': 'A', 'text': 'Excuse me, where is the nearest train station?'},
            {'speaker': 'B', 'text': 'Go straight two blocks, then turn right. You\'ll see it on your left.'},
            {'speaker': 'A', 'text': 'Thank you so much!'},
            {'speaker': 'B', 'text': 'You\'re welcome.'}
        ]
    },
]


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
