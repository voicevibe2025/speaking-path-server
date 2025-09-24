from django.test import TestCase

from ..serializers import UserRegistrationSerializer, UserLoginSerializer
from ..models import User


class UserRegistrationSerializerTests(TestCase):
    def test_password_mismatch_raises_error(self):
        serializer = UserRegistrationSerializer(data={
            "email": "mismatch@example.com",
            "password": "StrongPass123",
            "password_confirm": "DifferentPass456",
            "first_name": "Mismatch",
            "last_name": "User",
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_create_user_successfully(self):
        serializer = UserRegistrationSerializer(data={
            "email": "valid@example.com",
            "password": "StrongPass123",
            "password_confirm": "StrongPass123",
            "first_name": "Valid",
            "last_name": "User",
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "valid@example.com")
        self.assertTrue(user.check_password("StrongPass123"))


class UserLoginSerializerTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123"
        self.user = User.objects.create_user(
            email="login@example.com",
            username="login@example.com",
            password=self.password,
        )

    def test_valid_credentials(self):
        serializer = UserLoginSerializer(data={
            "email": self.user.email,
            "password": self.password,
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["user"], self.user)

    def test_invalid_credentials_raise_error(self):
        serializer = UserLoginSerializer(data={
            "email": self.user.email,
            "password": "WrongPassword",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("Unable to authenticate", str(serializer.errors))
