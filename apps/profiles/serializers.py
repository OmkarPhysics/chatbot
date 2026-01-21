from __future__ import annotations

from rest_framework import serializers

from apps.profiles.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ("id", "name", "email", "avatar", "created_at", "updated_at")
        read_only_fields = ("id", "email", "created_at", "updated_at")

    def validate_avatar(self, value):
        if not value:
            return value
        max_bytes = 2 * 1024 * 1024  # 2MB
        if getattr(value, "size", 0) > max_bytes:
            raise serializers.ValidationError("Avatar must be <= 2MB.")
        return value


class AdminUserProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True, required=False)
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ("id", "user_id", "name", "email", "avatar", "created_at", "updated_at")
        read_only_fields = ("id", "email", "created_at", "updated_at")

    def create(self, validated_data):
        user_id = validated_data.pop("user_id", None)
        if not user_id:
            raise serializers.ValidationError({"user_id": "This field is required."})
        return UserProfile.objects.create(user_id=user_id, **validated_data)

