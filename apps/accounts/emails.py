from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_verification_otp(*, email: str, otp: str) -> None:
    subject = "Verify your email"
    message = (
        "Use the OTP below to verify your email address:\n\n"
        f"{otp}\n\n"
        f"This code expires in {settings.EMAIL_OTP_TTL_SECONDS // 60} minutes."
    )
    _send_email(subject, message, email, otp_for_log=otp)


def send_password_reset_link(*, email: str, reset_link: str) -> None:
    subject = "Reset your password"
    message = (
        "Use the link below to reset your password:\n\n"
        f"{reset_link}\n\n"
        "If you did not request this, you can ignore this email."
    )
    _send_email(subject, message, email)


def _send_email(subject: str, message: str, recipient: str, *, otp_for_log: str | None = None) -> None:
    """Send email with fallback to console logging if SMTP fails."""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        logger.info(f"Email sent to {recipient}: {subject}")
        if otp_for_log and settings.DEBUG:
            logger.info(f"[DEBUG] OTP for {recipient}: {otp_for_log}")
    except Exception as e:
        # Log the error and print to console as fallback
        logger.warning(f"SMTP failed ({e}), printing email to console instead.")
        print("\n" + "=" * 60)
        print(f"EMAIL TO: {recipient}")
        print(f"SUBJECT: {subject}")
        print("-" * 60)
        print(message)
        print("=" * 60 + "\n")
