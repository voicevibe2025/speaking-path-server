from django.urls import reverse
from django.core import mail
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import User


class RegisterViewTests(APITestCase):
    def test_register_creates_user_and_returns_tokens(self):
        payload = {
            "email": "jane@example.com",
            "password": "StrongPass123",
            "password_confirm": "StrongPass123",
            "first_name": "Jane",
            "last_name": "Doe",
        }

        response = self.client.post(reverse("authentication:register"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(User.objects.filter(email="jane@example.com").exists())


class LoginViewTests(APITestCase):
    def setUp(self):
        self.password = "StrongPass123"
        self.user = User.objects.create_user(
            email="john@example.com",
            username="john@example.com",
            password=self.password,
            first_name="John",
            last_name="Smith",
        )

    def test_login_returns_tokens_for_valid_credentials(self):
        payload = {"email": self.user.email, "password": self.password}

        response = self.client.post(reverse("authentication:login"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], self.user.email)

    def test_login_rejects_invalid_credentials(self):
        payload = {"email": self.user.email, "password": "WrongPassword"}

        response = self.client.post(reverse("authentication:login"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unable to authenticate", str(response.data))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetRequestTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="reset@example.com",
            username="reset@example.com",
            password="StrongPass123",
        )

    def test_password_reset_sends_email_for_existing_user(self):
        payload = {"email": self.user.email}

        response = self.client.post(reverse("authentication:password_reset"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body.lower()
        self.assertIn("click the link below", email_body)
        self.assertIn("password-reset/confirm", email_body)

    def test_password_reset_returns_generic_success_for_unknown_email(self):
        payload = {"email": "unknown@example.com"}

        response = self.client.post(reverse("authentication:password_reset"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(mail.outbox), 0)
