"""
Shared serializers used across candidate and employer APIs.

Domain-specific serializers live in their respective packages:
  - api.candidate.serializers
  - api.employer.serializers
"""

from django.contrib.auth.models import User
from rest_framework import serializers

from core.models import (
    Application,
    ApplicationMatchScore,
    Interview,
    Job,
    Notification,
    ParsedResume,
    UserProfile,
)


# ── User & Profile ───────────────────────────────────────────────────────────


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id", "username"]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id", "user", "role", "full_name", "phone", "location",
            "company_name", "company_website", "company_description",
        ]
        read_only_fields = ["id", "role"]


# ── Jobs ─────────────────────────────────────────────────────────────────────


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight job serializer for list views."""
    company_name = serializers.CharField(source="employer.company_name", read_only=True)
    app_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Job
        fields = [
            "id", "title", "company", "company_name", "location",
            "salary", "category", "job_type", "status", "posted_at",
            "app_count",
        ]


class JobDetailSerializer(serializers.ModelSerializer):
    """Full job serializer with description and skills."""
    company_name = serializers.CharField(source="employer.company_name", read_only=True)
    required_skills = serializers.JSONField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id", "title", "company", "company_name", "description",
            "location", "salary", "category", "job_type", "status",
            "posted_at", "required_skills",
        ]


# ── Applications ─────────────────────────────────────────────────────────────


class ApplicationListSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    job_company = serializers.CharField(source="job.company", read_only=True)
    match_score = serializers.FloatField(
        source="match_score.overall_score", read_only=True, default=None
    )

    class Meta:
        model = Application
        fields = [
            "id", "job", "job_title", "job_company", "status",
            "applied_at", "match_score",
        ]
        read_only_fields = ["id", "status", "applied_at"]


class MatchScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationMatchScore
        fields = [
            "overall_score", "category_scores", "skill_details",
            "missing_skills", "computed_at",
        ]


class ParsedResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsedResume
        fields = [
            "parse_status", "parsed_data", "error_message",
            "source_file", "updated_at",
        ]


# ── Interviews ───────────────────────────────────────────────────────────────


class InterviewSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="application.user.username", read_only=True
    )
    job_title = serializers.CharField(
        source="application.job.title", read_only=True
    )

    class Meta:
        model = Interview
        fields = [
            "id", "application", "candidate_name", "job_title",
            "scheduled_time", "interview_type", "meeting_link",
            "notes", "status", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ── Notifications ────────────────────────────────────────────────────────────


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "is_read", "created_at"]
        read_only_fields = ["id", "message", "created_at"]
