"""
Management command to set user online/offline for testing
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Set user online or offline status for testing'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username or email')
        parser.add_argument(
            '--offline',
            action='store_true',
            help='Set user offline (default is online)'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        # Try to find user by username or email
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
                return
        
        if options['offline']:
            # Set last_activity to 10 minutes ago (offline)
            user.last_activity = timezone.now() - timedelta(minutes=10)
            status = 'OFFLINE'
        else:
            # Set last_activity to now (online)
            user.last_activity = timezone.now()
            status = 'ONLINE'
        
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ User "{user.username}" ({user.email}) set to {status}\n'
                f'   last_activity: {user.last_activity}'
            )
        )
