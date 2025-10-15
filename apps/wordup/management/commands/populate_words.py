from django.core.management.base import BaseCommand
from apps.wordup.models import Word


class Command(BaseCommand):
    help = 'Populate initial vocabulary words for WordUp feature'

    def handle(self, *args, **options):
        words_data = [
            # Beginner words
            {
                'word': 'abandon',
                'definition': 'To leave behind or give up completely',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'They had to abandon their car in the storm.'
            },
            {
                'word': 'brave',
                'definition': 'Showing courage and fearlessness',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was brave enough to speak in front of the crowd.'
            },
            {
                'word': 'curious',
                'definition': 'Eager to learn or know something',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'Children are naturally curious about the world.'
            },
            {
                'word': 'delicious',
                'definition': 'Having a very pleasant taste',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'The cake was absolutely delicious.'
            },
            {
                'word': 'enormous',
                'definition': 'Very large in size or quantity',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'The elephant was enormous compared to the dog.'
            },
            # Intermediate words
            {
                'word': 'ambiguous',
                'definition': 'Open to more than one interpretation; not clear',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'His answer was ambiguous and left us confused.'
            },
            {
                'word': 'benevolent',
                'definition': 'Well-meaning and kindly',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was known for her benevolent nature and generous donations.'
            },
            {
                'word': 'comprehend',
                'definition': 'To understand fully',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'It took me a while to comprehend the complex theory.'
            },
            {
                'word': 'diligent',
                'definition': 'Showing care and effort in work or duties',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was a diligent student who always completed his homework.'
            },
            {
                'word': 'eloquent',
                'definition': 'Fluent and persuasive in speaking or writing',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The speaker gave an eloquent presentation that moved the audience.'
            },
            # Advanced words
            {
                'word': 'aberration',
                'definition': 'A departure from what is normal or expected',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The warm weather in December was an aberration.'
            },
            {
                'word': 'gregarious',
                'definition': 'Fond of company; sociable',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was gregarious and loved attending social events.'
            },
            {
                'word': 'ephemeral',
                'definition': 'Lasting for a very short time',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The beauty of cherry blossoms is ephemeral, lasting only a week.'
            },
            {
                'word': 'ubiquitous',
                'definition': 'Present, appearing, or found everywhere',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'Smartphones have become ubiquitous in modern society.'
            },
            {
                'word': 'quintessential',
                'definition': 'Representing the most perfect example of something',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'She is the quintessential professional, always punctual and prepared.'
            },
        ]

        created_count = 0
        updated_count = 0

        for word_data in words_data:
            word, created = Word.objects.update_or_create(
                word=word_data['word'],
                defaults={
                    'definition': word_data['definition'],
                    'difficulty': word_data['difficulty'],
                    'part_of_speech': word_data['part_of_speech'],
                    'example_sentence': word_data['example_sentence'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {word.word}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {word.word}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new words, updated {updated_count} existing words.'
            )
        )
