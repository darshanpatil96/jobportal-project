"""
Shared API views — authentication, user profile, notifications.
Used by both candidate and employer frontends.
"""

from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import NotificationSerializer, UserProfileSerializer
from core.models import Notification, UserProfile


class RegisterSerializer:
    """Inline serializer for registration."""
    pass


class RegisterView(APIView):
    """Register a new user account."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from rest_framework import serializers

        class _Serializer(serializers.Serializer):
            username = serializers.CharField(max_length=150)
            email = serializers.EmailField()
            password = serializers.CharField(write_only=True, min_length=8)
            role = serializers.ChoiceField(choices=["jobseeker", "employer"])

        serializer = _Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if User.objects.filter(username=data["username"]).exists():
            return Response(
                {"error": "Username already taken."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(email=data["email"]).exists():
            return Response(
                {"error": "Email already registered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
        )
        UserProfile.objects.create(user=user, role=data["role"])

        return Response(
            {"id": user.id, "username": user.username, "role": data["role"]},
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(APIView):
    """Get or update the current authenticated user's profile."""

    def get(self, request):
        profile = getattr(request.user, "userprofile", None)
        if not profile:
            return Response({"error": "No profile found."}, status=404)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile = getattr(request.user, "userprofile", None)
        if not profile:
            return Response({"error": "No profile found."}, status=404)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class NotificationListView(generics.ListAPIView):
    """List notifications for the current user."""

    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )[:50]
