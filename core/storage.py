"""
Custom storage backends for VoiceVibe
"""
import os
import requests
from urllib.parse import urljoin
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    """
    Custom storage backend for Supabase Storage using native REST API
    
    This storage backend uses Supabase's native Storage API rather than
    the S3-compatible interface, as Supabase doesn't provide traditional
    S3 access keys.
    """
    
    def __init__(self, **options):
        super().__init__(**options)
        self.supabase_url = os.environ.get('SUPABASE_URL', '').rstrip('/')
        self.supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
        self.bucket_name = os.environ.get('SUPABASE_STORAGE_BUCKET_NAME', 'avatars')
        
        # Extract project reference from URL for API calls
        if self.supabase_url:
            # URL format: https://[project-ref].supabase.co
            self.project_ref = self.supabase_url.split('//')[1].split('.')[0]
        else:
            self.project_ref = ''
    
    def _get_headers(self):
        """Get headers for Supabase API requests"""
        return {
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'apikey': self.supabase_key
        }
    
    def _get_upload_headers(self, content_type='application/octet-stream'):
        """Get headers for file upload"""
        return {
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': content_type,
            'apikey': self.supabase_key
        }
    
    def _save(self, name, content):
        """
        Save file to Supabase Storage
        """
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and Service Role Key are required")
        
        # API endpoint for uploading files
        upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{name}"
        
        # Determine content type
        content_type = getattr(content, 'content_type', 'application/octet-stream')
        
        # Prepare file data
        content.seek(0)
        file_data = content.read()
        
        try:
            response = requests.post(
                upload_url,
                data=file_data,
                headers=self._get_upload_headers(content_type)
            )
            
            if response.status_code in [200, 201]:
                return name
            else:
                error_msg = f"Upload failed with status {response.status_code}: {response.text}"
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to save file {name} to Supabase Storage: {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Request failed when saving {name} to Supabase Storage: {e}")
            raise
    
    def delete(self, name):
        """
        Delete file from Supabase Storage
        """
        if not self.supabase_url or not self.supabase_key:
            return False
            
        delete_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{name}"
        
        try:
            response = requests.delete(
                delete_url,
                headers=self._get_headers()
            )
            return response.status_code in [200, 204]
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to delete file {name} from Supabase Storage: {e}")
            return False
    
    def exists(self, name):
        """
        Check if file exists in Supabase Storage
        """
        if not self.supabase_url or not self.supabase_key:
            return False
            
        info_url = f"{self.supabase_url}/storage/v1/object/info/{self.bucket_name}/{name}"
        
        try:
            response = requests.get(
                info_url,
                headers=self._get_headers()
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def url(self, name):
        """
        Return the public URL for the file
        """
        if not self.supabase_url:
            return name
            
        return f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{name}"
    
    def size(self, name):
        """
        Get file size
        """
        if not self.supabase_url or not self.supabase_key:
            return 0
            
        info_url = f"{self.supabase_url}/storage/v1/object/info/{self.bucket_name}/{name}"
        
        try:
            response = requests.get(
                info_url,
                headers=self._get_headers()
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('metadata', {}).get('size', 0)
        except Exception:
            pass
        return 0
    
    def get_valid_name(self, name):
        """
        Return a filename that is valid for the storage system
        """
        return name
    
    def get_available_name(self, name, max_length=None):
        """
        Return a filename that's free on the target storage system
        """
        # For Supabase, we can overwrite files, so just return the name
        return name
    
    def generate_filename(self, filename):
        """
        Generate a filename based on the provided filename
        """
        return filename


@deconstructible 
class AvatarSupabaseStorage(SupabaseStorage):
    """
    Specialized Supabase storage for user avatars with local fallback
    """
    
    def __init__(self):
        # Check if Supabase is configured (using correct environment variables)
        supabase_configured = bool(
            os.environ.get('SUPABASE_URL') and 
            os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        if not supabase_configured:
            # Use local storage as fallback
            from django.core.files.storage import FileSystemStorage
            self._use_local_fallback = True
            self._local_storage = FileSystemStorage(location='media/avatars/')
        else:
            self._use_local_fallback = False
            super().__init__()
            # Override bucket name for avatars specifically
            self.bucket_name = os.environ.get('SUPABASE_AVATARS_BUCKET_NAME', 'avatars')
    
    def _save(self, name, content):
        """Save with fallback to local storage if Supabase is not configured"""
        if self._use_local_fallback:
            return self._local_storage._save(name, content)
        return super()._save(name, content)
    
    def delete(self, name):
        """Delete with fallback to local storage if Supabase is not configured"""
        if self._use_local_fallback:
            return self._local_storage.delete(name)
        return super().delete(name)
    
    def exists(self, name):
        """Check existence with fallback to local storage if Supabase is not configured"""
        if self._use_local_fallback:
            return self._local_storage.exists(name)
        return super().exists(name)
    
    def url(self, name):
        """Get URL with fallback to local storage if Supabase is not configured"""
        if self._use_local_fallback:
            return self._local_storage.url(name)
        return super().url(name)
    
    def get_available_name(self, name, max_length=None):
        """
        Generate a filename for avatars - allow overwriting
        """
        if self._use_local_fallback:
            return self._local_storage.get_available_name(name, max_length)
        # For Supabase, we allow overwriting, so just return the name
        return name
