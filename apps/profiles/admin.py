from __future__ import annotations

from django.contrib import admin

from apps.profiles.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "user")
    search_fields = ("email", "name", "user__email")

