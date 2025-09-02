import os
import django

# Setup Django
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.users.models import UserProfile as UsersUserProfile
from apps.gamification.models import UserLevel
from apps.speaking_journey.models import TopicProgress, PhraseProgress, UserProfile as SpeakingUserProfile

from apps.users.models import UserProfile, UserAchievement


class Command(BaseCommand):
    help = "Reset a user's profile stats and achievements without deleting the account"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="User email to reset")

    def handle(self, *args, **kwargs):
        email = kwargs["email"]
        User = get_user_model()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ User with email {email} not found"))
            return

        # Reset UserProfile stats
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.total_practice_time = 0
        profile.streak_days = 0
        profile.last_practice_date = None
        profile.save()

        # Delete all achievements
        achievements_deleted, _ = UserAchievement.objects.filter(user=user).delete()

        self.stdout.write(self.style.SUCCESS(
            f"🎉 Reset complete for {email}: "
            f"profile stats cleared, {achievements_deleted} achievements removed."
        ))

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
