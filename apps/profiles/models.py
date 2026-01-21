from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


def avatar_upload_to(instance: "UserProfile", filename: str) -> str:
    return f"avatars/{instance.user_id}/{filename}"


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")

    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Mirror user email (credential source of truth).
        self.email = (getattr(self.user, "email", "") or "").strip().lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.email}"


