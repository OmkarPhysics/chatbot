from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase


User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthFlowTests(APITestCase):
    def _extract_first_otp(self) -> str:
        self.assertGreaterEqual(len(mail.outbox), 1)
        body = mail.outbox[-1].body
        m = re.search(r"\b(\d{6})\b", body)
        self.assertIsNotNone(m, f"Could not find OTP in email body:\n{body}")
        return m.group(1)

    def _extract_reset_params(self):
        self.assertGreaterEqual(len(mail.outbox), 1)
        body = mail.outbox[-1].body
        # Find the first URL-ish token in the email body
        m = re.search(r"(https?://\S+)", body)
        self.assertIsNotNone(m, f"Could not find reset link in email body:\n{body}")
        url = m.group(1)
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        return qs["uidb64"][0], qs["token"][0]

    def test_register_verify_login_profile_logout_refresh_fail(self):
        email = "alice@example.com"
        password = "SuperSecurePass123!"

        # Register
        res = self.client.post("/api/auth/register/", {"email": email, "password": password, "name": "Alice"}, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["email"], email)

        # Login should fail before verification (simplejwt returns 401 for inactive accounts)
        res = self.client.post("/api/auth/login/", {"email": email, "password": password}, format="json")
        self.assertEqual(res.status_code, 401, res.data)

        # Verify email with OTP from email
        otp = self._extract_first_otp()
        res = self.client.post("/api/auth/verify-email/", {"email": email, "otp": otp}, format="json")
        self.assertEqual(res.status_code, 200, res.data)

        # Login success
        res = self.client.post("/api/auth/login/", {"email": email, "password": password}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        access = res.data["access"]
        refresh = res.data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        # Profile should exist (created via signals)
        res = self.client.get("/api/profile/me/")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["email"], email)

        # Update name
        res = self.client.patch("/api/profile/me/", {"name": "Alice Updated"}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["name"], "Alice Updated")

        # Logout (blacklist refresh)
        self.client.credentials()  # logout uses refresh token only
        res = self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json")
        self.assertEqual(res.status_code, 200, res.data)

        # Refresh should now fail due to blacklist
        res = self.client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(res.status_code, 401, res.data)

    def test_forgot_and_reset_password(self):
        email = "bob@example.com"
        password = "OriginalPass123!"
        new_password = "NewPass123!"

        # Create verified/active user directly
        user = User.objects.create_user(email=email, password=password)
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])

        # Forgot password should always return 200
        res = self.client.post("/api/auth/forgot-password/", {"email": email}, format="json")
        self.assertEqual(res.status_code, 200, res.data)

        uidb64, token = self._extract_reset_params()

        # Reset password
        res = self.client.post(
            "/api/auth/reset-password/",
            {"uidb64": uidb64, "token": token, "new_password": new_password},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.data)

        # Login works with new password
        res = self.client.post("/api/auth/login/", {"email": email, "password": new_password}, format="json")
        self.assertEqual(res.status_code, 200, res.data)

