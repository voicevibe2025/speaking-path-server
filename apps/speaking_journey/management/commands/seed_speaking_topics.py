from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max, F
from django.core.management.base import CommandError
from apps.speaking_journey.models import Topic, EnglishLevel
from . import topics as topics_module


class Command(BaseCommand):
    help = 'Updates or creates Speaking Journey topics from the topics list, preserving existing user progress.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            choices=[c for c, _ in EnglishLevel.choices],
            help=(
                "When provided, seeds topics for the given English level using a matching "
                "<LEVEL>_TOPICS list in topics.py (e.g., BEGINNER_TOPICS)."
            ),
        )
        parser.add_argument(
            '--start-seq',
            type=int,
            default=None,
            help=(
                "Optional starting sequence for newly created topics when --level is specified. "
                "If omitted, the command will append after the current maximum sequence."
            ),
        )
        parser.add_argument(
            '--reflow',
            action='store_true',
            help=(
                "When used together with --level and --start-seq, shifts all existing topics with "
                "sequence >= start-seq upward by the number of topics being seeded, creating space "
                "for the new range without collisions. Safe and atomic."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Updating Speaking Journey topics...'))

        created_count = 0
        updated_count = 0

        level = options.get('level')

        if level:
            # Seed for a specific English level using <LEVEL>_TOPICS list
            topics_attr = f"{level}_TOPICS"
            if not hasattr(topics_module, topics_attr):
                raise CommandError(
                    f"topics.py missing '{topics_attr}'. Please define a list of dicts for {level}."
                )
            topics_list = getattr(topics_module, topics_attr)

            reserved_count = len(topics_list or [])

            # Determine starting sequence for new topics
            if options.get('start_seq') is not None:
                start_seq = int(options['start_seq'])
                current_seq = start_seq - 1

                # If not reflowing, ensure the reserved window is free
                if not options.get('reflow', False):
                    if reserved_count > 0:
                        end_seq = start_seq + reserved_count - 1
                        if Topic.objects.filter(sequence__gte=start_seq, sequence__lte=end_seq).exists():
                            raise CommandError(
                                f"Sequence range {start_seq}-{end_seq} is already occupied. "
                                f"Pass --reflow to safely make room, or choose a higher --start-seq."
                            )
                else:
                    # Reflow: shift existing topics to make room for the reserved window
                    if reserved_count > 0:
                        Topic.objects.filter(sequence__gte=start_seq).update(
                            sequence=F('sequence') + reserved_count
                        )
            else:
                max_seq = Topic.objects.aggregate(ms=Max('sequence'))['ms'] or 0
                current_seq = int(max_seq)

            for item in topics_list:
                title = str(item['title']).strip()

                # Look up existing topic by (title, difficulty)
                existing_topic = Topic.objects.filter(title=title, difficulty=level).first()

                topic_data = {
                    'title': title,
                    'description': item.get('description', ''),
                    'material_lines': item.get('material', []),
                    'conversation_example': item.get('conversation', []),
                    'vocabulary': item.get('vocabulary', []),
                    'fluency_practice_prompt': item.get('fluency_practice_prompt', []),
                    'is_active': True,
                    'difficulty': level,
                }

                if existing_topic:
                    # Update existing topic in-place; do not change sequence to avoid collisions
                    for field, value in topic_data.items():
                        setattr(existing_topic, field, value)
                    # If start_seq was provided, align existing topic into the reserved window
                    if options.get('start_seq') is not None:
                        current_seq += 1
                        existing_topic.sequence = current_seq
                    existing_topic.save()
                    updated_count += 1
                    self.stdout.write(f" - UPDATED [{level}]: {existing_topic.sequence}. {title}")
                else:
                    # Create new topic with next available sequence
                    current_seq += 1
                    Topic.objects.create(sequence=current_seq, **topic_data)
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f" - CREATED [{level}]: {current_seq}. {title}"
                    ))

        else:
            # Default behavior (backward-compatible): use TOPICS list and reset sequences to 1..N
            if not hasattr(topics_module, 'TOPICS'):
                raise CommandError("topics.py missing 'TOPICS' list.")
            topics_list = getattr(topics_module, 'TOPICS')

            # Update or create topics from the source list
            for idx, item in enumerate(topics_list, start=1):
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
