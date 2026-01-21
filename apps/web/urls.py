from __future__ import annotations

from django.urls import path

from apps.web import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_page, name="register_page"),
    path("verify-email/", views.verify_email_page, name="verify_email_page"),
    path("login/", views.login_page, name="login_page"),
    path("profile/", views.profile_page, name="profile_page"),
    path("forgot-password/", views.forgot_password_page, name="forgot_password_page"),
    path("reset-password/", views.reset_password_page, name="reset_password_page"),
]

