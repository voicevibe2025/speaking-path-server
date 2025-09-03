from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Register a new user with hard-coded values"

    def handle(self, *args, **kwargs):
        # Hard-coded values (you can later replace with inputs)
        first_name = "Rina"
        last_name = "Rina"
        email = "gamedev456545@gmail.com"
        password = "btm12345"
        retype_password = "btm12345"
        accept_terms = True

        # Check password match
        if password != retype_password:
            self.stdout.write(self.style.ERROR("Passwords do not match"))
            return

        # Check terms
        if not accept_terms:
            self.stdout.write(self.style.ERROR("User must accept terms and conditions"))
            return

        # Check if user exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"User with email {email} already exists"))
            return

        # Create user
        user = User.objects.create_user(
            username=email,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )

        self.stdout.write(self.style.SUCCESS(f"User {user.email} registered successfully!"))
