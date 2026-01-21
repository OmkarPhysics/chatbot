from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    SimpleJWT already keys off get_user_model().USERNAME_FIELD, which is `email` in our custom User.
    We override validation to explicitly reject unverified/inactive users.
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        if not getattr(user, "email_verified", False):
            raise serializers.ValidationError("Email is not verified.")
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")
        return data

