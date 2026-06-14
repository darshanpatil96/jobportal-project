"""
Custom DRF permissions for role-based access control.

These permissions enforce the candidate/employer boundary at the API level.
"""

from rest_framework.permissions import BasePermission


class IsCandidate(BasePermission):
    """Allow access only to authenticated job seekers."""

    message = "This endpoint is for job seekers only."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, "userprofile", None)
        return profile is not None and profile.role == "jobseeker"


class IsEmployer(BasePermission):
    """Allow access only to authenticated employers."""

    message = "This endpoint is for employers only."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, "userprofile", None)
        return profile is not None and profile.role == "employer"



class IsApplicationOwner(BasePermission):
    """Allow access only to the candidate who owns the application."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsJobOwner(BasePermission):
    """Allow access only to the employer who owns the job."""

    def has_object_permission(self, request, view, obj):
        profile = getattr(request.user, "userprofile", None)
        return profile is not None and obj.employer == profile
