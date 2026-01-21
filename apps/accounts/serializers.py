from __future__ import annotations

import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.emails import send_password_reset_link, send_verification_otp
from apps.accounts.models import EmailOTP


User = get_user_model()


def generate_numeric_otp(length: int) -> str:
    alphabet = string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        email = validated_data["email"].strip().lower()
        password = validated_data["password"]
        name = (validated_data.get("name") or "").strip()

        try:
            user = User.objects.create_user(email=email, password=password)
        except IntegrityError:
            # Race-condition safe duplicate rejection
            raise serializers.ValidationError({"email": "A user with this email already exists."})

        # Ensure profile exists and store the provided name (profile is created by signals).
        try:
            profile = user.profile
        except Exception:
            profile = None
        if profile is not None and name:
            profile.name = name
            profile.save(update_fields=["name"])

        otp = generate_numeric_otp(settings.EMAIL_OTP_LENGTH)
        EmailOTP.objects.create(
            user=user,
            purpose=EmailOTP.Purpose.VERIFY_EMAIL,
            code_hash=make_password(otp),
            expires_at=timezone.now() + timedelta(seconds=settings.EMAIL_OTP_TTL_SECONDS),
        )
        send_verification_otp(email=user.email, otp=otp)
        return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        otp = attrs["otp"].strip()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No user found for this email."})

        otp_qs = (
            EmailOTP.objects.filter(user=user, purpose=EmailOTP.Purpose.VERIFY_EMAIL, used_at__isnull=True)
            .order_by("-created_at")
        )
        otp_obj = otp_qs.first()
        if not otp_obj:
            raise serializers.ValidationError({"otp": "No active OTP found. Please register again."})
        if otp_obj.is_expired:
            raise serializers.ValidationError({"otp": "OTP expired. Please register again."})
        if not check_password(otp, otp_obj.code_hash):
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        attrs["user"] = user
        attrs["otp_obj"] = otp_obj
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        otp_obj = validated_data["otp_obj"]
        otp_obj.used_at = timezone.now()
        otp_obj.save(update_fields=["used_at"])

        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def create(self, validated_data):
        email = validated_data["email"].strip().lower()
        request = self.context.get("request")

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return {"sent": False}

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Send link to the minimal HTML page (which posts to the API).
        if request is not None:
            reset_link = request.build_absolute_uri(f"/reset-password/?uidb64={uidb64}&token={token}")
        else:
            reset_link = f"/reset-password/?uidb64={uidb64}&token={token}"

        send_password_reset_link(email=user.email, reset_link=reset_link)
        return {"sent": True}


class ResetPasswordSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uidb64"]))
            user = User.objects.get(pk=uid)
        except Exception:
            raise serializers.ValidationError({"uidb64": "Invalid uid."})

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        user.set_password(validated_data["new_password"])
        user.save(update_fields=["password"])
        return user

