from django.core.management.base import BaseCommand
from django.db import transaction
from apps.speaking_journey.models import Topic


TOPICS = [
    {
        'title': 'Greetings and Introductions',
        'description': 'Learn common phrases for greeting people and introducing yourself in everyday situations such as meeting new classmates or colleagues.',
        'material': [
            'Hi, I\'m Sarah.',
            'Nice to meet you.',
            'Where are you from?',
            'I\'m from Jakarta.',
            'How are you doing?',
            'I\'m doing well, thanks.'
        ],
        'conversation': [
            {'speaker': 'A', 'text': 'Hey, I don\'t think we\'ve met before. I\'m Sarah.'},
            {'speaker': 'B', 'text': 'Hi Sarah, nice to meet you. I\'m David.'},
            {'speaker': 'A', 'text': 'Nice to meet you too, David. Where are you from?'},
            {'speaker': 'B', 'text': 'I\'m from Bandung. How about you?'},
            {'speaker': 'A', 'text': 'I\'m from Jakarta.'},
            {'speaker': 'B', 'text': 'Cool! So, how are you doing today?'},
            {'speaker': 'A', 'text': 'I\'m doing well, thanks. And you?'},
            {'speaker': 'B', 'text': 'Pretty good, thanks for asking.'}
        ]
    },
{
    'title': 'Daily Activities',
    'description': 'Talk about your daily routine, including mornings, commute, work or school, and evening activities.',
    'material': [
        'I usually wake up around 6:30.',
        'I grab a quick breakfast before work.',
        'I take the bus to the office every day.',
        'After work, I sometimes hang out with friends or just relax at home.',
        'On weekends, I like to sleep in and spend time with my family.'
    ],
    'conversation': [
        {'speaker': 'A', 'text': 'What time do you usually wake up?'},
        {'speaker': 'B', 'text': 'Around 6:30. I check my phone, then get ready for work.'},
        {'speaker': 'A', 'text': 'Do you eat breakfast at home or on the way?'},
        {'speaker': 'B', 'text': 'Usually at home. Just something quick like bread and coffee.'},
        {'speaker': 'A', 'text': 'How do you get to work?'},
        {'speaker': 'B', 'text': 'I take the bus. It takes about 30 minutes.'},
        {'speaker': 'A', 'text': 'What do you usually do after work?'},
        {'speaker': 'B', 'text': 'Sometimes I go out with friends, but most days I just relax and watch TV.'},
        {'speaker': 'A', 'text': 'Sounds nice. How about weekends?'},
        {'speaker': 'B', 'text': 'I usually sleep in, do some chores, and spend time with my family.'}
    ]
},
{
    'title': 'Asking for Directions',
    'description': 'Politely ask for and follow directions in public places like streets, stations, or malls.',
    'material': [
        'Excuse me, do you know where the train station is?',
        'How far is it from here?',
        'Should I go straight or turn at the next corner?',
        'Thanks a lot for your help.',
        'I’m not from around here.'
    ],
    'conversation': [
        {'speaker': 'A', 'text': 'Excuse me, could you tell me how to get to the train station?'},
        {'speaker': 'B', 'text': 'Sure. Just go straight for about five minutes, then turn left at the traffic light.'},
        {'speaker': 'A', 'text': 'Is it walking distance, or should I take a bus?'},
        {'speaker': 'B', 'text': 'It’s pretty close, you can walk. It’s only a couple of blocks away.'},
        {'speaker': 'A', 'text': 'Okay, so straight ahead and then left at the light, right?'},
        {'speaker': 'B', 'text': 'That’s right. You’ll see the station on your right-hand side.'},
        {'speaker': 'A', 'text': 'Perfect, thanks a lot!'},
        {'speaker': 'B', 'text': 'No problem. Have a good day!'}
    ]
},
        {
        'title': 'Hobbies and Interests',
        'description': 'Learn to talk about your hobbies, what you do in your free time, and ask others about their interests.',
        'material': [
            'What do you do for fun?',
            'In my free time, I like to read books.',
            'I\'m really into hiking.',
            'Do you have any hobbies?',
            'I enjoy playing guitar and watching movies.',
            'How long have you been doing that?'
        ],
        'conversation': [
            {'speaker': 'A', 'text': 'So, what do you like to do in your free time?'},
            {'speaker': 'B', 'text': 'I\'m really into photography. I love taking pictures of nature on the weekends.'},
            {'speaker': 'A', 'text': 'That sounds amazing! What about you? Do you have any hobbies?'},
            {'speaker': 'B', 'text': 'I enjoy cooking. I try to make a new recipe every Sunday.'},
            {'speaker': 'A', 'text': 'Oh, really? How long have you been doing that?'},
            {'speaker': 'B', 'text': 'For about a year now. It\'s a great way to relax.'}
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
