# app/management/commands/delete_user.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Delete a user account by email"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email of the user to delete")

    def handle(self, *args, **kwargs):
        email = kwargs["email"]
        User = get_user_model()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ No user found with {email}"))
            return

        # Confirm deletion (optional: remove this if you want auto-delete without prompt)
        confirm = input(f"⚠️ Are you sure you want to delete {email}? (yes/no): ")
        if confirm.lower() != "yes":
            self.stdout.write(self.style.WARNING("❌ Aborted"))
            return

        user.delete()
        self.stdout.write(self.style.SUCCESS(f"🗑️ User {email} has been deleted."))
