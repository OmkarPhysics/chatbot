from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail


def send_verification_otp(*, email: str, otp: str) -> None:
    subject = "Verify your email"
    message = (
        "Use the OTP below to verify your email address:\n\n"
        f"{otp}\n\n"
        f"This code expires in {settings.EMAIL_OTP_TTL_SECONDS // 60} minutes."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)


def send_password_reset_link(*, email: str, reset_link: str) -> None:
    subject = "Reset your password"
    message = (
        "Use the link below to reset your password:\n\n"
        f"{reset_link}\n\n"
        "If you did not request this, you can ignore this email."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)

