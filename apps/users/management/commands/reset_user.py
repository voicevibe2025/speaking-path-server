import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yourproject.settings")
django.setup()

from django.contrib.auth import get_user_model
from users.models import UserProfile as UsersUserProfile
from gamification.models import UserLevel
from speaking_journey.models import TopicProgress, PhraseProgress, UserProfile as SpeakingUserProfile

User = get_user_model()

def reset_user(email):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        print(f"User with email {email} not found")
        return

    # Reset profiles
    UsersUserProfile.objects.filter(user=user).update(points=0)
    SpeakingUserProfile.objects.filter(user=user).update(progress=0)

    # Reset gamification
    UserLevel.objects.filter(user=user).update(level=0, xp=0)

    # Reset progress
    TopicProgress.objects.filter(user=user).update(progress=0)
    PhraseProgress.objects.filter(user=user).update(mastered=False)

    print(f"🎉 Reset progress for {email} complete")

if __name__ == "__main__":
    reset_user("gamedev456545@gmail.com")
