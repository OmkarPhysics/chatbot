from __future__ import annotations

from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.profiles.models import UserProfile
from apps.profiles.serializers import AdminUserProfileSerializer, UserProfileSerializer


class MeProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        return Response(UserProfileSerializer(profile).data)

    def patch(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        # Deleting your profile deletes your user account (profile cascades).
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = UserProfile.objects.select_related("user").all().order_by("-created_at")
    serializer_class = AdminUserProfileSerializer

