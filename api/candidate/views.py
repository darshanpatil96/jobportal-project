"""
Candidate API views — job browsing, applications, saved jobs, dashboard.

All views require authentication. Most require IsCandidate permission.
Job browsing (list/detail) is open to all authenticated users.
"""

from django.db.models import Count, Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsApplicationOwner, IsCandidate
from api.serializers import (
    ApplicationListSerializer,
    JobDetailSerializer,
    JobListSerializer,
    MatchScoreSerializer,
    ParsedResumeSerializer,
)
from core.models import (
    Application,
    ApplicationTimelineEvent,
    Job,
    SavedJob,
)
from core.services.candidate.jobs import filter_jobs, get_categories, get_job_filters
from core.hiring.pipeline import PipelineService
from core.hiring.workflow import ApplicationWorkflowService


# ── Jobs ─────────────────────────────────────────────────────────────────────


class JobListView(generics.ListAPIView):
    """Browse open jobs with filtering and search."""

    serializer_class = JobListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Job.objects.filter(status="Open").annotate(
            app_count=Count("application")
        )
        filters = get_job_filters(self.request)
        return filter_jobs(qs, filters)


class JobDetailView(generics.RetrieveAPIView):
    """Get full job details."""

    serializer_class = JobDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Job.objects.filter(status="Open")


# ── Applications ─────────────────────────────────────────────────────────────


class ApplicationListView(generics.ListAPIView):
    """List the current user's applications."""

    serializer_class = ApplicationListSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return (
            Application.objects.filter(user=self.request.user)
            .select_related("job", "match_score")
            .order_by("-applied_at")
        )


class ApplicationDetailView(APIView):
    """Get detailed application info including match score and parsed resume."""

    permission_classes = [IsCandidate]

    def get(self, request, pk):
        try:
            app = Application.objects.select_related(
                "job", "match_score", "parsed_resume"
            ).get(pk=pk, user=request.user)
        except Application.DoesNotExist:
            return Response({"error": "Not found."}, status=404)

        data = ApplicationListSerializer(app).data
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
        return Response(data)


class ApplyJobView(APIView):
    """Submit a job application."""

    permission_classes = [IsCandidate]

    def post(self, request):
        job_id = request.data.get("job_id")
        if not job_id:
            return Response(
                {"error": "job_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            job = Job.objects.get(pk=job_id, status="Open")
        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=404)

        if Application.objects.filter(user=request.user, job=job).exists():
            return Response(
                {"error": "Already applied to this job."},
                status=status.HTTP_409_CONFLICT,
            )

        app = Application.objects.create(
            user=request.user,
            job=job,
            status="Applied",
            cover_letter=request.data.get("cover_letter", ""),
            qualification=request.data.get("qualification", ""),
            phone=request.data.get("phone", ""),
            experience=request.data.get("experience", ""),
        )
        ApplicationWorkflowService.process_new_application(app)

        return Response(
            ApplicationListSerializer(app).data, status=status.HTTP_201_CREATED
        )


class WithdrawApplicationView(APIView):
    """Withdraw an application."""

    permission_classes = [IsCandidate]

    def post(self, request, pk):
        try:
            app = Application.objects.get(pk=pk, user=request.user)
        except Application.DoesNotExist:
            return Response({"error": "Not found."}, status=404)

        try:
            PipelineService.transition(
                app, "Withdrawn", updated_by=request.user, notes="Withdrawn via API"
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"status": "withdrawn"})


class ApplicationTimelineView(APIView):
    """Get timeline events for an application."""

    permission_classes = [IsCandidate]

    def get(self, request, pk):
        try:
            app = Application.objects.get(pk=pk, user=request.user)
        except Application.DoesNotExist:
            return Response({"error": "Not found."}, status=404)

        events = ApplicationTimelineEvent.objects.filter(
            application=app
        ).order_by("-created_at").values(
            "event_type", "message", "metadata", "created_at"
        )
        return Response(list(events))


# ── Saved Jobs ───────────────────────────────────────────────────────────────


class SavedJobListView(generics.ListAPIView):
    """List saved/bookmarked jobs."""

    serializer_class = JobListSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        saved_ids = SavedJob.objects.filter(
            user=self.request.user
        ).values_list("job_id", flat=True)
        return Job.objects.filter(id__in=saved_ids).order_by("-posted_at")


class ToggleSaveJobView(APIView):
    """Save or unsave a job."""

    permission_classes = [IsCandidate]

    def post(self, request):
        job_id = request.data.get("job_id")
        if not job_id:
            return Response(
                {"error": "job_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=404)

        saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        if not created:
            saved.delete()
            return Response({"saved": False})
        return Response({"saved": True}, status=status.HTTP_201_CREATED)


# ── Dashboard ────────────────────────────────────────────────────────────────


class CandidateDashboardView(APIView):
    """Candidate dashboard summary data."""

    permission_classes = [IsCandidate]

    def get(self, request):
        user = request.user
        total_applications = Application.objects.filter(user=user).count()
        total_saved = SavedJob.objects.filter(user=user).count()

        recent_apps = (
            Application.objects.filter(user=user)
            .select_related("job", "match_score")
            .order_by("-applied_at")[:5]
        )

        # Simple recommendations based on applied categories
        applied_categories = set(
            Application.objects.filter(user=user)
            .values_list("job__category", flat=True)
            .distinct()
        )
        recommended = (
            Job.objects.filter(status="Open", category__in=applied_categories)
            .exclude(application__user=user)
            .order_by("-posted_at")[:5]
        )

        return Response({
            "total_applications": total_applications,
            "total_saved": total_saved,
            "recent_applications": ApplicationListSerializer(recent_apps, many=True).data,
            "recommended_jobs": JobListSerializer(recommended, many=True).data,
        })
