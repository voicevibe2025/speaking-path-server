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
            {
                'word': 'frequent',
                'definition': 'Happening often or at short intervals',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'He is a frequent visitor to the library.'
            },
            {
                'word': 'gentle',
                'definition': 'Having a mild, kind, or tender temperament or character',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'The dog was very gentle with the children.'
            },
            {
                'word': 'happy',
                'definition': 'Feeling or showing pleasure or contentment',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was happy to see her friends again.'
            },
            {
                'word': 'imagine',
                'definition': 'To form a mental image or concept of',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'Can you imagine a world without music?'
            },
            {
                'word': 'journey',
                'definition': 'An act of traveling from one place to another',
                'difficulty': 'beginner',
                'part_of_speech': 'noun',
                'example_sentence': 'The journey to the mountains was long but beautiful.'
            },
            {
                'word': 'kind',
                'definition': 'Having a friendly, generous, and considerate nature.',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'It was very kind of you to help me.'
            },
            {
                'word': 'laugh',
                'definition': 'Make the spontaneous sounds and movements of the face and body that are the instinctive expressions of lively amusement and sometimes also of derision.',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'She started to laugh uncontrollably.'
            },
            {
                'word': 'music',
                'definition': 'Vocal or instrumental sounds (or both) combined in such a way as to produce beauty of form, harmony, and expression of emotion.',
                'difficulty': 'beginner',
                'part_of_speech': 'noun',
                'example_sentence': 'The music was playing softly in the background.'
            },
            {
                'word': 'ocean',
                'definition': 'A very large expanse of sea, in particular each of the main areas into which the sea is divided geographically.',
                'difficulty': 'beginner',
                'part_of_speech': 'noun',
                'example_sentence': 'The ocean waves crashed against the shore.'
            },
            {
                'word': 'quiet',
                'definition': 'Making little or no noise.',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'The library was a quiet place to study.'
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
            {
                'word': 'facilitate',
                'definition': 'To make an action or process easy or easier',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'The new software will facilitate data analysis.'
            },
            {
                'word': 'harmonious',
                'definition': 'Forming a pleasing or consistent whole',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'They lived in a harmonious relationship with their neighbors.'
            },
            {
                'word': 'illustrate',
                'definition': 'To explain or make clear by using examples, charts, or pictures',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'The teacher used diagrams to illustrate the concept.'
            },
            {
                'word': 'meticulous',
                'definition': 'Showing great attention to detail; very careful and precise',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was meticulous in his preparation for the presentation.'
            },
            {
                'word': 'navigate',
                'definition': 'To plan and direct the route or course of a ship, aircraft, or other form of transport, especially by using instruments or maps',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'It was difficult to navigate through the dense fog.'
            },
            {
                'word': 'nostalgia',
                'definition': 'A sentimental longing or wistful affection for the past, typically for a period or place with happy personal associations.',
                'difficulty': 'intermediate',
                'part_of_speech': 'noun',
                'example_sentence': 'He was filled with nostalgia for his college days.'
            },
            {
                'word': 'obsolete',
                'definition': 'No longer produced or used; out of date.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The typewriter has become obsolete with the advent of computers.'
            },
            {
                'word': 'pragmatic',
                'definition': 'Dealing with things sensibly and realistically in a way that is based on practical rather than theoretical considerations.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'She took a pragmatic approach to solving the problem.'
            },
            {
                'word': 'resilient',
                'definition': 'Able to withstand or recover quickly from difficult conditions.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'Children are often more resilient than adults.'
            },
            {
                'word': 'skeptical',
                'definition': 'Not easily convinced; having doubts or reservations.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was skeptical about the claims made in the advertisement.'
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
            {
                'word': 'cacophony',
                'definition': 'A harsh, discordant mixture of sounds',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'A cacophony of car horns filled the street during rush hour.'
            },
            {
                'word': 'deleterious',
                'definition': 'Causing harm or damage',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'Smoking has many deleterious effects on health.'
            },
            {
                'word': 'esoteric',
                'definition': 'Intended for or likely to be understood by only a small number of people with a specialized knowledge or interest',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The book was full of esoteric references that only a few scholars could understand.'
            },
            {
                'word': 'paradigm',
                'definition': 'A typical example or pattern of something; a model',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The new discovery shifted the scientific paradigm.'
            },
            {
                'word': 'serendipity',
                'definition': 'The occurrence and development of events by chance in a happy or beneficial way',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'Meeting her was pure serendipity; it changed my life for the better.'
            },
            {
                'word': 'sycophant',
                'definition': 'A person who acts obsequiously toward someone important in order to gain advantage.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The king was surrounded by sycophants who praised his every decision.'
            },
            {
                'word': 'taciturn',
                'definition': 'Reserved or uncommunicative in speech; saying little.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was a taciturn man who rarely spoke about his feelings.'
            },
            {
                'word': 'unctuous',
                'definition': 'Excessively flattering or ingratiating; oily.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'His unctuous praise made her feel uncomfortable.'
            },
            {
                'word': 'veracity',
                'definition': 'Conformity to facts; accuracy.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The veracity of his story was questionable.'
            },
            {
                'word': 'zenith',
                'definition': 'The time at which something is most powerful or successful.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The Roman Empire reached its zenith in the 2nd century AD.'
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
