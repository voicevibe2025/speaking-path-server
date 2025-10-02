"""
Management command to migrate existing avatars from local storage to Supabase Storage
"""
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from apps.users.models import UserProfile


class Command(BaseCommand):
    help = 'Migrate existing avatars from local storage to Supabase Storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if Supabase storage is not configured',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Check if Supabase is configured
        required_env_vars = [
            'SUPABASE_ACCESS_KEY_ID',
            'SUPABASE_SECRET_ACCESS_KEY', 
            'SUPABASE_ENDPOINT_URL'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars and not force:
            self.stdout.write(
                self.style.ERROR(
                    f'Missing required environment variables: {", ".join(missing_vars)}\n'
                    'Set these variables or use --force to continue anyway.'
                )
            )
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual changes will be made'))

        # Get all user profiles with avatars
        profiles_with_avatars = UserProfile.objects.exclude(avatar='').exclude(avatar__isnull=True)
        total_profiles = profiles_with_avatars.count()
        
        if total_profiles == 0:
            self.stdout.write(self.style.SUCCESS('No avatars found to migrate'))
            return

        self.stdout.write(f'Found {total_profiles} avatars to migrate')
        
        migrated_count = 0
        error_count = 0
        
        for profile in profiles_with_avatars:
            try:
                if dry_run:
                    self.stdout.write(f'Would migrate avatar for user {profile.user.id}: {profile.avatar.name}')
                    migrated_count += 1
                else:
                    # Try to get the local file path - handle different storage backends
                    local_path = None
                    try:
                        # For FileSystemStorage, we can get the path
                        if hasattr(profile.avatar, 'path'):
                            local_path = profile.avatar.path
                        elif hasattr(profile.avatar.storage, 'path'):
                            local_path = profile.avatar.storage.path(profile.avatar.name)
                        else:
                            # Construct path manually for default Django setup
                            from django.conf import settings
                            local_path = os.path.join(settings.MEDIA_ROOT, profile.avatar.name)
                    except Exception as path_error:
                        self.stdout.write(
                            self.style.WARNING(f'Could not determine local path for user {profile.user.id}: {path_error}')
                        )
                    
                    if local_path and os.path.exists(local_path):
                        try:
                            # Read the local file
                            with open(local_path, 'rb') as f:
                                file_content = f.read()
                            
                            # Get the filename
                            filename = os.path.basename(profile.avatar.name)
                            
                            # Create a temporary storage instance to upload to Supabase
                            from core.storage import AvatarSupabaseStorage
                            supabase_storage = AvatarSupabaseStorage()
                            
                            # Create new path for Supabase (using user ID for uniqueness)
                            file_ext = filename.split('.')[-1] if '.' in filename else 'jpg'
                            new_filename = f"avatars/user_{profile.user.id}.{file_ext}"
                            
                            # Create content file
                            content_file = ContentFile(file_content, name=new_filename)
                            
                            # Save to Supabase storage directly
                            uploaded_name = supabase_storage._save(new_filename, content_file)
                            
                            # Update the profile's avatar field to point to the new location
                            old_avatar_name = profile.avatar.name
                            profile.avatar.name = uploaded_name
                            profile.save()
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Migrated avatar for user {profile.user.id}: {old_avatar_name} -> {uploaded_name}'
                                )
                            )
                            migrated_count += 1
                            
                            # Clean up local file (optional)
                            try:
                                os.remove(local_path)
                                self.stdout.write(f'Cleaned up local file: {local_path}')
                            except Exception as cleanup_error:
                                self.stdout.write(
                                    self.style.WARNING(f'Could not clean up local file {local_path}: {cleanup_error}')
                                )
                                
                        except Exception as upload_error:
                            self.stdout.write(
                                self.style.ERROR(f'Failed to upload avatar for user {profile.user.id}: {upload_error}')
                            )
                            error_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Local avatar file not found for user {profile.user.id}: {profile.avatar.name} (path: {local_path})'
                            )
                        )
                        error_count += 1
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error migrating avatar for user {profile.user.id}: {e}')
                )
                error_count += 1
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN COMPLETE: Would migrate {migrated_count} avatars')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Migration complete: {migrated_count} avatars migrated successfully, {error_count} errors'
                )
            )
            
            if error_count > 0:
                self.stdout.write(
                    self.style.WARNING('Some avatars could not be migrated. Check the errors above.')
                )
