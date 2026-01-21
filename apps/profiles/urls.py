from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.profiles import views


router = DefaultRouter()
router.register(r"admin/profiles", views.AdminProfileViewSet, basename="admin_profiles")


urlpatterns = [
    path("me/", views.MeProfileView.as_view(), name="me_profile"),
    path("", include(router.urls)),
]

