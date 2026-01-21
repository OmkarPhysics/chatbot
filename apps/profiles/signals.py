from __future__ import annotations

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.profiles.models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, created, **kwargs):
    # Create profile automatically; safe for future profile extension.
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        # Keep mirrored email in sync if user email changes.
        try:
            profile = instance.profile
        except Exception:
            UserProfile.objects.get_or_create(user=instance)
            return
        if profile.email != instance.email:
            profile.email = instance.email
            profile.save(update_fields=["email"])

