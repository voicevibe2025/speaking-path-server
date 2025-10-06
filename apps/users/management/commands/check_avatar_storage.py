"""
Management command to check avatar storage status
"""
from django.core.management.base import BaseCommand
from apps.users.models import UserProfile
from core.storage import AvatarSupabaseStorage


class Command(BaseCommand):
    help = 'Check which avatars are already in Supabase Storage'

    def handle(self, *args, **options):
        # Check if Supabase is configured
        storage = AvatarSupabaseStorage()
        
        if storage._use_local_fallback:
            self.stdout.write(
                self.style.WARNING('Supabase is not configured - using local storage')
            )
            return
        
        self.stdout.write(self.style.SUCCESS('Supabase Storage is configured'))
        self.stdout.write(f'Bucket: {storage.bucket_name}')
        self.stdout.write(f'URL: {storage.supabase_url}\n')
        
        # Get all user profiles with avatars
        profiles_with_avatars = UserProfile.objects.exclude(avatar='').exclude(avatar__isnull=True)
        total_profiles = profiles_with_avatars.count()
        
        if total_profiles == 0:
            self.stdout.write(self.style.SUCCESS('No avatar fields set in database'))
            return

        self.stdout.write(f'Found {total_profiles} profiles with avatar field set\n')
        
        exists_count = 0
        missing_count = 0
        
        for profile in profiles_with_avatars:
            avatar_name = profile.avatar.name
            exists = storage.exists(avatar_name)
            
            if exists:
                exists_count += 1
                url = storage.url(avatar_name)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ User {profile.user.id}: {avatar_name}')
                )
                self.stdout.write(f'  URL: {url}')
            else:
                missing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'✗ User {profile.user.id}: {avatar_name} - NOT FOUND in Supabase')
                )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Summary: {exists_count} avatars exist in Supabase'))
        if missing_count > 0:
            self.stdout.write(self.style.WARNING(f'         {missing_count} avatars missing from Supabase'))
        self.stdout.write('='*60)
