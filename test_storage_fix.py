#!/usr/bin/env python
"""
Quick test script to debug Supabase Storage issue
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from core.storage import AvatarSupabaseStorage
from django.core.files.base import ContentFile

def test_storage():
    print("Testing Supabase Storage...")
    
    # Check environment variables
    print(f"SUPABASE_URL: {os.environ.get('SUPABASE_URL', 'Not set')}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'Not set')[:10]}...")
    
    try:
        # Initialize storage
        storage = AvatarSupabaseStorage()
        print(f"Storage initialized: {type(storage)}")
        
        if hasattr(storage, '_use_local_fallback'):
            print(f"Using local fallback: {storage._use_local_fallback}")
        
        # Test file upload
        test_content = b'Test avatar content'
        test_file = ContentFile(test_content, name='test_avatar.txt')
        
        filename = storage.save('test_avatar.txt', test_file)
        print(f"File saved as: {filename}")
        
        # Get URL
        url = storage.url(filename)
        print(f"File URL: {url}")
        
        # Clean up
        storage.delete(filename)
        print("Test file deleted")
        
        print("✅ Storage test passed!")
        
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_storage()
