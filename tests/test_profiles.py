from __future__ import annotations

from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APITestCase


User = get_user_model()


class ProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
        )
        self.user.email_verified = True
        self.user.is_active = True
        self.user.save(update_fields=["email_verified", "is_active"])

        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123!",
        )

    def _login(self, user):
        res = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "TestPass123!" if user == self.user else "AdminPass123!"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def _create_test_image(self, size_bytes=1024):
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        content = buffer.read()

        if len(content) < size_bytes:
            content += b"\x00" * (size_bytes - len(content))

        return SimpleUploadedFile(
            name="test_avatar.png",
            content=content[:size_bytes] if len(content) > size_bytes else content,
            content_type="image/png",
        )

    def test_get_own_profile(self):
        self._login(self.user)
        res = self.client.get("/api/profile/me/")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["email"], self.user.email)
        self.assertIn("name", res.data)
        self.assertIn("created_at", res.data)

    def test_update_profile_name(self):
        self._login(self.user)
        res = self.client.patch("/api/profile/me/", {"name": "New Name"}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["name"], "New Name")

        res = self.client.get("/api/profile/me/")
        self.assertEqual(res.data["name"], "New Name")

    def test_cannot_change_email_via_profile(self):
        self._login(self.user)
        original_email = self.user.email
        res = self.client.patch("/api/profile/me/", {"email": "hacker@example.com"}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["email"], original_email)

    def test_delete_profile_deletes_user(self):
        self._login(self.user)
        user_id = self.user.id
        res = self.client.delete("/api/profile/me/")
        self.assertEqual(res.status_code, 204)
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_unauthenticated_cannot_access_profile(self):
        res = self.client.get("/api/profile/me/")
        self.assertEqual(res.status_code, 401)

    def test_avatar_upload_size_limit(self):
        self._login(self.user)

        large_image = self._create_test_image(size_bytes=3 * 1024 * 1024)
        res = self.client.patch(
            "/api/profile/me/",
            {"avatar": large_image},
            format="multipart",
        )
        self.assertEqual(res.status_code, 400, res.data)
        self.assertIn("avatar", res.data)

    def test_admin_can_list_all_profiles(self):
        self._login(self.admin)
        res = self.client.get("/api/profile/admin/profiles/")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertGreaterEqual(len(res.data), 2)

    def test_admin_can_update_any_profile(self):
        self._login(self.admin)
        profile_id = self.user.profile.id
        res = self.client.patch(
            f"/api/profile/admin/profiles/{profile_id}/",
            {"name": "Admin Updated"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["name"], "Admin Updated")

    def test_regular_user_cannot_access_admin_endpoint(self):
        self._login(self.user)
        res = self.client.get("/api/profile/admin/profiles/")
        self.assertEqual(res.status_code, 403)
