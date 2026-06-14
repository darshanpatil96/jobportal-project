"""
Employer API views — ATS dashboard, job management, candidate pipeline,
interviews, analytics.

All views require IsEmployer permission.
"""

from django.db.models import Count, F
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsEmployer, IsJobOwner
from api.serializers import (
    ApplicationListSerializer,
    InterviewSerializer,
    JobDetailSerializer,
    JobListSerializer,
    MatchScoreSerializer,
    ParsedResumeSerializer,
)
from core.models import Application, Interview, Job, UserProfile
from core.hiring.employer_queries import (
    get_analytics,
    get_employer_stats,
    get_recent_applications,
    get_upcoming_interviews,
)
from core.hiring.interviews import InterviewService
from core.hiring.pipeline import PipelineService


def _get_employer_profile(user):
    return UserProfile.objects.get(user=user, role="employer")


# ── Dashboard ────────────────────────────────────────────────────────────────


class EmployerDashboardView(APIView):
    """Employer dashboard summary — stats, recent apps, upcoming interviews."""

    permission_classes = [IsEmployer]

    def get(self, request):
        profile = _get_employer_profile(request.user)
        stats = get_employer_stats(profile)
        recent = get_recent_applications(profile, limit=5)
        upcoming = get_upcoming_interviews(profile, limit=5)

        return Response({
            "stats": stats,
            "recent_applications": ApplicationListSerializer(recent, many=True).data,
            "upcoming_interviews": InterviewSerializer(upcoming, many=True).data,
        })


# ── Jobs ─────────────────────────────────────────────────────────────────────


class EmployerJobListView(generics.ListAPIView):
    """List jobs posted by the current employer."""

    serializer_class = JobListSerializer
    permission_classes = [IsEmployer]

    def get_queryset(self):
        profile = _get_employer_profile(self.request.user)
        return (
            Job.objects.filter(employer=profile)
            .annotate(app_count=Count("application"))
            .order_by("-posted_at")
        )


class EmployerJobCreateView(APIView):
    """Create a new job posting."""

    permission_classes = [IsEmployer]

    def post(self, request):
        profile = _get_employer_profile(request.user)
        serializer = JobDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = Job(
            employer=profile,
            title=serializer.validated_data["title"],
            company=serializer.validated_data.get("company", profile.company_name),
            description=serializer.validated_data["description"],
            location=serializer.validated_data["location"],
            salary=serializer.validated_data.get("salary", ""),
            category=serializer.validated_data["category"],
            job_type=serializer.validated_data.get("job_type", "Full-Time"),
            status=serializer.validated_data.get("status", "Open"),
        )
        job.save()

        return Response(JobDetailSerializer(job).data, status=status.HTTP_201_CREATED)


class EmployerJobDetailView(APIView):
    """Get job details with application stats."""

    permission_classes = [IsEmployer]

    def get(self, request, pk):
        profile = _get_employer_profile(request.user)
        try:
            job = Job.objects.annotate(app_count=Count("application")).get(
                pk=pk, employer=profile
            )
        except Job.DoesNotExist:
            return Response({"error": "Not found."}, status=404)

        data = JobDetailSerializer(job).data
        data["app_count"] = job.app_count
        return Response(data)


class EmployerJobUpdateView(APIView):
    """Update a job posting."""

    permission_classes = [IsEmployer]

    def patch(self, request, pk):
        profile = _get_employer_profile(request.user)
        try:
            job = Job.objects.get(pk=pk, employer=profile)
        except Job.DoesNotExist:
            return Response({"error": "Not found."}, status=404)

        allowed_fields = [
            "title", "description", "location", "salary",
            "category", "job_type", "status",
        ]
        for field in allowed_fields:
            if field in request.data:
                setattr(job, field, request.data[field])
        job.save()

        return Response(JobDetailSerializer(job).data)


# ── Candidates / Applications ────────────────────────────────────────────────


class EmployerCandidateListView(generics.ListAPIView):
    """List all applications to the employer's jobs."""

    serializer_class = ApplicationListSerializer
    permission_classes = [IsEmployer]

    def get_queryset(self):
        profile = _get_employer_profile(self.request.user)
        qs = (
            Application.objects.filter(job__employer=profile)
            .exclude(status="Withdrawn")
            .select_related("user", "job", "match_score")
            .order_by(
                F("match_score__overall_score").desc(nulls_last=True), "-applied_at"
            )
        )
        # Optional filters
        job_id = self.request.query_params.get("job")
        status_filter = self.request.query_params.get("status")
        min_match = self.request.query_params.get("min_match")

        if job_id:
            qs = qs.filter(job_id=job_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if min_match:
            qs = qs.filter(match_score__overall_score__gte=float(min_match))
        return qs


class EmployerCandidateDetailView(APIView):
    """Get full candidate application details."""

    permission_classes = [IsEmployer]

    def get(self, request, pk):
        profile = _get_employer_profile(request.user)
        try:
            app = (
                Application.objects.select_related(
                    "user", "job", "match_score", "parsed_resume"
                )
                .prefetch_related("timeline_events", "interviews")
                .get(pk=pk, job__employer=profile)
            )
        except Application.DoesNotExist:
            return Response({"error": "Not found."}, status=404)

        data = ApplicationListSerializer(app).data
        data["candidate"] = {
            "username": app.user.username,
            "email": app.user.email,
            "phone": app.phone,
            "qualification": app.qualification,
            "experience": app.experience,
            "cover_letter": app.cover_letter,
        }
        data["match_score"] = (
            MatchScoreSerializer(app.match_score).data
            if hasattr(app, "match_score") and app.match_score
            else None
        )
        data["parsed_resume"] = (
            ParsedResumeSerializer(app.parsed_resume).data
            if hasattr(app, "parsed_resume") and app.parsed_resume
            else None
        )
        data["allowed_statuses"] = PipelineService.get_allowed_next_statuses(
            app.status
        )
        data["interviews"] = InterviewSerializer(
            app.interviews.all(), many=True
        ).data

        return Response(data)


class UpdateCandidateStatusView(APIView):
    """Move a candidate through the hiring pipeline."""

    permission_classes = [IsEmployer]

    def post(self, request, pk):
        profile = _get_employer_profile(request.user)
        new_status = request.data.get("status")
        notes = request.data.get("notes", "")

        if not new_status:
            return Response(
                {"error": "status is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            app = Application.objects.get(pk=pk, job__employer=profile)
        except Application.DoesNotExist:
            return Response({"error": "Not found."}, status=404)

        try:
            PipelineService.transition(
                app, new_status, updated_by=request.user, notes=notes
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"status": app.status})


# ── Interviews ───────────────────────────────────────────────────────────────


class EmployerInterviewListView(generics.ListAPIView):
    """List all interviews for the employer's jobs."""

    serializer_class = InterviewSerializer
    permission_classes = [IsEmployer]

    def get_queryset(self):
        profile = _get_employer_profile(self.request.user)
        qs = Interview.objects.filter(
            application__job__employer=profile
        ).select_related("application__user", "application__job")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("-scheduled_time")


class ScheduleInterviewView(APIView):
    """Schedule an interview for a candidate."""

    permission_classes = [IsEmployer]

    def post(self, request):
        profile = _get_employer_profile(request.user)
        app_id = request.data.get("application_id")
        scheduled_time = request.data.get("scheduled_time")
        interview_type = request.data.get("interview_type", "Online")
        meeting_link = request.data.get("meeting_link", "")
        notes = request.data.get("notes", "")

        if not app_id or not scheduled_time:
            return Response(
                {"error": "application_id and scheduled_time are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            app = Application.objects.get(pk=app_id, job__employer=profile)
        except Application.DoesNotExist:
            return Response({"error": "Application not found."}, status=404)

        from django.utils.dateparse import parse_datetime

        dt = parse_datetime(scheduled_time)
        if not dt:
            return Response(
                {"error": "Invalid datetime format."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            interview = InterviewService.schedule(
                application=app,
                scheduled_by=request.user,
                scheduled_time=dt,
                interview_type=interview_type,
                meeting_link=meeting_link,
                notes=notes,
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            InterviewSerializer(interview).data, status=status.HTTP_201_CREATED
        )


class UpdateInterviewStatusView(APIView):
    """Update interview status (Completed, Cancelled, Rescheduled)."""

    permission_classes = [IsEmployer]

    def post(self, request, pk):
        profile = _get_employer_profile(request.user)
        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"error": "status is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            interview = Interview.objects.get(
                pk=pk, application__job__employer=profile
            )
        except Interview.DoesNotExist:
            return Response({"error": "Not found."}, status=404)

        try:
            InterviewService.update_status(interview, new_status)
        except Exception as exc:
            return Response(
                {"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(InterviewSerializer(interview).data)


# ── Analytics ────────────────────────────────────────────────────────────────


class EmployerAnalyticsView(APIView):
    """Employer analytics — pipeline counts, applications per job, etc."""

    permission_classes = [IsEmployer]

    def get(self, request):
        profile = _get_employer_profile(request.user)
        stats = get_employer_stats(profile)
        analytics = get_analytics(profile)

        return Response({
            "stats": stats,
            "pipeline_counts": list(analytics["pipeline_counts"]),
            "applications_per_job": list(analytics["applications_per_job"]),
            "applications_per_category": list(analytics["applications_per_category"]),
        })
