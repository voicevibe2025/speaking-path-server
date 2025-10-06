"""
Management command to clean up avatar references for files that don't exist in storage
"""
from django.core.management.base import BaseCommand
from apps.users.models import UserProfile
from core.storage import AvatarSupabaseStorage


class Command(BaseCommand):
    help = 'Clean up avatar field references for files that do not exist in Supabase Storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Check if Supabase is configured
        storage = AvatarSupabaseStorage()
        
        if storage._use_local_fallback:
            self.stdout.write(
                self.style.WARNING('Supabase is not configured - using local storage')
            )
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual changes will be made\n'))
        
        # Get all user profiles with avatars
        profiles_with_avatars = UserProfile.objects.exclude(avatar='').exclude(avatar__isnull=True)
        total_profiles = profiles_with_avatars.count()
        
        if total_profiles == 0:
            self.stdout.write(self.style.SUCCESS('No avatar fields to check'))
            return

        self.stdout.write(f'Checking {total_profiles} profiles...\n')
        
        cleaned_count = 0
        kept_count = 0
        
        for profile in profiles_with_avatars:
            avatar_name = profile.avatar.name
            exists = storage.exists(avatar_name)
            
            if not exists:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(f'Would clean user {profile.user.id}: {avatar_name}')
                    )
                else:
                    # Clear the avatar field
                    profile.avatar = ''
                    profile.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Cleaned user {profile.user.id}: {avatar_name}')
                    )
                cleaned_count += 1
            else:
                kept_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would clean {cleaned_count} missing avatar references')
            )
            self.stdout.write(f'Would keep {kept_count} existing avatars')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Cleaned {cleaned_count} missing avatar references')
            )
            self.stdout.write(self.style.SUCCESS(f'Kept {kept_count} existing avatars'))
            if cleaned_count > 0:
                self.stdout.write('\nThese users can now upload new profile pictures.')
        self.stdout.write('='*60)
