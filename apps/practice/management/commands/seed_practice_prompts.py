from django.core.management.base import BaseCommand
from django.db import transaction
from apps.practice.models import PracticePrompt


PROMPTS = [
    {
        'text': 'Introduce yourself to a new colleague in two minutes.',
        'category': 'INTRODUCTION',
        'difficulty': 'BEGINNER',
        'hints': ['Mention your name', 'Talk about your role', 'Share a hobby'],
        'target_duration': 60,
        'cultural_context': 'Workplace etiquette values clarity and friendliness.',
        'scenario_type': 'BUSINESS',
    },
    {
        'text': 'Describe your daily routine on a weekday.',
        'category': 'DAILY_LIFE',
        'difficulty': 'BEGINNER',
        'hints': ['Morning activities', 'Commute', 'Evening habits'],
        'target_duration': 45,
        'cultural_context': None,
        'scenario_type': 'GENERAL',
    },
    {
        'text': 'Ask for directions to the nearest train station politely.',
        'category': 'TRAVEL',
        'difficulty': 'INTERMEDIATE',
        'hints': ['Greet first', 'Use polite forms', 'Confirm understanding'],
        'target_duration': 30,
        'cultural_context': 'Consider formal vs informal address depending on the culture.',
        'scenario_type': 'SOCIAL',
    },
]


class Command(BaseCommand):
    help = 'Seeds Practice prompts. Idempotent: updates or creates by unique text. Use --reset to deactivate missing.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Deactivate prompts not present in PROMPTS list')

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding Practice prompts...'))

        seen_texts = set()
        created_count = 0
        updated_count = 0

        for item in PROMPTS:
            text = item['text'].strip()
            seen_texts.add(text)
            defaults = {
                'category': item['category'],
                'difficulty': item['difficulty'],
                'hints': item.get('hints', []),
                'target_duration': item.get('target_duration', 30),
                'cultural_context': item.get('cultural_context'),
                'scenario_type': item.get('scenario_type', 'GENERAL'),
                'is_active': True,
            }
            obj, created = PracticePrompt.objects.update_or_create(
                text=text,
                defaults=defaults,
            )
            if created:
                created_count += 1
                self.stdout.write(f" - CREATED: {text[:60]}...")
            else:
                updated_count += 1
                self.stdout.write(f" - UPDATED: {text[:60]}...")

        if options.get('reset'):
            deactivated = PracticePrompt.objects.exclude(text__in=seen_texts).update(is_active=False)
            if deactivated:
                self.stdout.write(self.style.WARNING(f'Deactivated {deactivated} prompts not in PROMPTS list'))

        total_active = PracticePrompt.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(
            f'Done. Created: {created_count}, Updated: {updated_count}, Active total: {total_active}'
        ))
