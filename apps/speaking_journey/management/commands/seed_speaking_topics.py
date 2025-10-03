from django.core.management.base import BaseCommand
from django.db import transaction
from apps.speaking_journey.models import Topic
from .topics import TOPICS

TOPICS = TOPICS


class Command(BaseCommand):
    help = 'Updates or creates Speaking Journey topics from the topics list, preserving existing user progress.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Updating Speaking Journey topics...'))

        created_count = 0
        updated_count = 0

        # Update or create topics from the source list
        for idx, item in enumerate(TOPICS, start=1):
            title = item['title'].strip()
            
            # Try to find existing topic by sequence or title
            existing_topic = Topic.objects.filter(sequence=idx).first()
            if not existing_topic:
                existing_topic = Topic.objects.filter(title=title).first()
            
            topic_data = {
                'title': title,
                'description': item.get('description', ''),
                'material_lines': item.get('material', []),
                'conversation_example': item.get('conversation', []),
                'vocabulary': item.get('vocabulary', []),
                'fluency_practice_prompt': item.get('fluency_practice_prompt', []),
                'is_active': True,
            }
            
            if existing_topic:
                # Update existing topic
                for field, value in topic_data.items():
                    setattr(existing_topic, field, value)
                existing_topic.sequence = idx
                existing_topic.save()
                updated_count += 1
                self.stdout.write(f" - UPDATED: {idx}. {title}")
            else:
                # Create new topic
                Topic.objects.create(sequence=idx, **topic_data)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f" - CREATED: {idx}. {title}"))

        total = Topic.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted: {created_count} created, {updated_count} updated. Total topics: {total}'
        ))
