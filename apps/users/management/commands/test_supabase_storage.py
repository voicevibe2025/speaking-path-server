"""
Management command to test Supabase Storage connectivity and configuration
"""
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.storage import AvatarSupabaseStorage


class Command(BaseCommand):
    help = 'Test Supabase Storage connectivity and configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--upload-test',
            action='store_true',
            help='Test uploading a small test file',
        )

    def handle(self, *args, **options):
        upload_test = options['upload_test']
        
        self.stdout.write(self.style.WARNING('Testing Supabase Storage Configuration...'))
        
        # Check environment variables
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_ROLE_KEY'
        ]
        
        self.stdout.write('\n1. Checking environment variables:')
        for var in required_vars:
            value = os.environ.get(var)
            if value:
                # Mask sensitive values
                if 'KEY' in var:
                    display_value = value[:10] + '...' if len(value) > 10 else '***'
                else:
                    display_value = value
                self.stdout.write(f'   ✓ {var}: {display_value}')
            else:
                self.stdout.write(f'   ✗ {var}: Not set')
        
        # Check optional variables
        optional_vars = [
            'SUPABASE_STORAGE_BUCKET_NAME',
            'SUPABASE_AVATARS_BUCKET_NAME'
        ]
        
        self.stdout.write('\n2. Optional environment variables:')
        for var in optional_vars:
            value = os.environ.get(var, 'Not set (using default)')
            self.stdout.write(f'   • {var}: {value}')
        
        # Test storage initialization
        self.stdout.write('\n3. Testing storage initialization:')
        try:
            storage = AvatarSupabaseStorage()
            if hasattr(storage, '_use_local_fallback') and storage._use_local_fallback:
                self.stdout.write('   ⚠ Using local storage fallback (Supabase not configured)')
            else:
                self.stdout.write('   ✓ Supabase storage initialized successfully')
        except Exception as e:
            self.stdout.write(f'   ✗ Failed to initialize storage: {e}')
            return
        
        # Test file upload if requested
        if upload_test:
            self.stdout.write('\n4. Testing file upload:')
            try:
                # Create a small test file
                test_content = b'This is a test avatar file for Supabase Storage'
                test_file = ContentFile(test_content, name='test_avatar.txt')
                
                # Upload the file
                filename = storage.save('test_uploads/test_avatar.txt', test_file)
                self.stdout.write(f'   ✓ File uploaded successfully: {filename}')
                
                # Get the URL
                url = storage.url(filename)
                self.stdout.write(f'   ✓ File URL: {url}')
                
                # Check if file exists
                exists = storage.exists(filename)
                self.stdout.write(f'   ✓ File exists check: {exists}')
                
                # Clean up - delete the test file
                storage.delete(filename)
                self.stdout.write('   ✓ Test file cleaned up')
                
            except Exception as e:
                self.stdout.write(f'   ✗ Upload test failed: {e}')
                # Try to provide more specific error information
                if '401' in str(e) or 'Unauthorized' in str(e):
                    self.stdout.write('     → Check your SUPABASE_SERVICE_ROLE_KEY')
                elif '404' in str(e) or 'Not Found' in str(e):
                    self.stdout.write('     → Check your bucket name and ensure it exists in Supabase')
                elif 'Connection' in str(e):
                    self.stdout.write('     → Check your SUPABASE_URL')
                elif '403' in str(e) or 'Forbidden' in str(e):
                    self.stdout.write('     → Check bucket permissions and RLS policies')
        
        # Summary
        self.stdout.write('\n' + '='*50)
        supabase_configured = all(os.environ.get(var) for var in required_vars)
        
        if supabase_configured:
            self.stdout.write(self.style.SUCCESS('✓ Supabase Storage appears to be configured'))
            if not upload_test:
                self.stdout.write('   Run with --upload-test to test actual file operations')
        else:
            self.stdout.write(self.style.WARNING('⚠ Supabase Storage is not fully configured'))
            self.stdout.write('   Avatars will use local storage (not persistent across deployments)')
            self.stdout.write('   See SUPABASE_AVATAR_SETUP.md for configuration instructions')
        
        self.stdout.write('')
