"""
Management command to seed Batam cultural groups
"""
from django.core.management.base import BaseCommand
from apps.users.models import Group


class Command(BaseCommand):
    help = 'Seed Batam cultural groups with descriptions and colors'

    def handle(self, *args, **options):
        groups_data = [
            {
                'name': 'gonggong',
                'display_name': 'Gonggong',
                'description': 'Named after the iconic Gonggong ship, a symbol of Batam\'s maritime heritage and connection to the sea.',
                'icon': '🚢',
                'color': '#1E88E5',  # Ocean Blue
            },
            {
                'name': 'pantun',
                'display_name': 'Pantun',
                'description': 'Celebrating the traditional Malay art of pantun poetry, emphasizing creativity and cultural expression.',
                'icon': '📜',
                'color': '#8E24AA',  # Purple
            },
            {
                'name': 'zapin',
                'display_name': 'Zapin',
                'description': 'Honoring the graceful Zapin dance, a traditional Malay performance art that brings communities together.',
                'icon': '💃',
                'color': '#E91E63',  # Pink
            },
            {
                'name': 'hang_nadim',
                'display_name': 'Hang Nadim',
                'description': 'Named after the legendary hero Hang Nadim, symbolizing wisdom, courage, and problem-solving.',
                'icon': '⚔️',
                'color': '#F57C00',  # Orange
            },
            {
                'name': 'barelang',
                'display_name': 'Barelang',
                'description': 'Inspired by the iconic Barelang Bridge, representing connection, unity, and Batam\'s modern development.',
                'icon': '🌉',
                'color': '#00897B',  # Teal
            },
            {
                'name': 'bulan_serindit',
                'display_name': 'Bulan Serindit',
                'description': 'Named after the beautiful Serindit bird and moon, symbolizing nature, beauty, and harmony.',
                'icon': '🌙',
                'color': '#5E35B1',  # Deep Purple
            },
            {
                'name': 'selayar',
                'display_name': 'Selayar',
                'description': 'Honoring the Selayar ethnic group, celebrating cultural diversity and traditional wisdom.',
                'icon': '🏝️',
                'color': '#43A047',  # Green
            },
            {
                'name': 'tanjung_ulma',
                'display_name': 'Tanjung Ulma',
                'description': 'Named after a historic cape in Batam, representing exploration, adventure, and discovery.',
                'icon': '🧭',
                'color': '#D32F2F',  # Red
            },
            {
                'name': 'pulau_putri',
                'display_name': 'Pulau Putri',
                'description': 'Inspired by Princess Island, symbolizing beauty, grace, and the natural wonders of Batam.',
                'icon': '👑',
                'color': '#FDD835',  # Yellow
            },
            {
                'name': 'temiang',
                'display_name': 'Temiang',
                'description': 'Named after a local area in Batam, representing community roots, growth, and shared heritage.',
                'icon': '🌴',
                'color': '#6D4C41',  # Brown
            },
        ]

        created_count = 0
        updated_count = 0

        for data in groups_data:
            group, created = Group.objects.update_or_create(
                name=data['name'],
                defaults={
                    'display_name': data['display_name'],
                    'description': data['description'],
                    'icon': data['icon'],
                    'color': data['color'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created group: {group.display_name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Updated group: {group.display_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully seeded {created_count} new groups and updated {updated_count} existing groups!'
            )
        )
