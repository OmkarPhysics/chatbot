from __future__ import annotations

from django.shortcuts import render


def home(request):
    return render(request, "web/home.html")


def register_page(request):
    return render(request, "web/register.html")


def verify_email_page(request):
    return render(request, "web/verify_email.html")


def login_page(request):
    return render(request, "web/login.html")


def profile_page(request):
    return render(request, "web/profile.html")


def forgot_password_page(request):
    return render(request, "web/forgot_password.html")


def reset_password_page(request):
    return render(request, "web/reset_password.html")

