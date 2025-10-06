"""
Quick test script to verify online status is working
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.users.serializers import UserProfileSerializer

User = get_user_model()

print("\n" + "="*60)
print("TESTING ONLINE STATUS FEATURE")
print("="*60 + "\n")

# Check all users
users = User.objects.all()[:5]  # First 5 users

for user in users:
    try:
        profile = user.profile
        serializer = UserProfileSerializer(profile)
        
        print(f"User: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  Last Activity: {user.last_activity}")
        print(f"  isOnline (computed): {serializer.data.get('isOnline', 'NOT FOUND')}")
        
        if user.last_activity:
            diff = timezone.now() - user.last_activity
            minutes = diff.total_seconds() / 60
            print(f"  Minutes since active: {minutes:.2f}")
        
        print()
    except Exception as e:
        print(f"  Error: {e}\n")

print("="*60)
print("✅ If 'isOnline' shows True/False, backend is working!")
print("📱 Now rebuild the Android app to see the green dot")
print("="*60 + "\n")
