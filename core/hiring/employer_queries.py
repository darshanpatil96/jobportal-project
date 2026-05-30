"""Query helpers for the employer portal."""

from django.db.models import Count, Q, F
from django.utils import timezone

from core.models import Application, Interview, Job


def get_employer_profile(user):
    return user.userprofile


def get_employer_stats(employer_profile):
    jobs_qs = Job.objects.filter(employer=employer_profile)
    apps_qs = Application.objects.filter(job__employer=employer_profile).exclude(
        status="Withdrawn"
    )
    return {
        "total_jobs": jobs_qs.count(),
        "total_applications": apps_qs.count(),
        "open_jobs": jobs_qs.filter(status="Open").count(),
        "scheduled_interviews": Interview.objects.filter(
            application__job__employer=employer_profile,
            status="Scheduled",
            scheduled_time__gte=timezone.now(),
        ).count(),
    }


def get_recent_applications(employer_profile, limit=5):
    return (
        Application.objects.filter(job__employer=employer_profile)
        .exclude(status="Withdrawn")
        .select_related("user", "job", "match_score")
        .order_by("-applied_at")[:limit]
    )


def get_upcoming_interviews(employer_profile, limit=5):
    return (
        Interview.objects.filter(
            application__job__employer=employer_profile,
            status="Scheduled",
            scheduled_time__gte=timezone.now(),
        )
        .select_related("application__user", "application__job")
        .order_by("scheduled_time")[:limit]
    )


def get_employer_jobs(employer_profile, status_filter=None):
    qs = (
        Job.objects.filter(employer=employer_profile)
        .annotate(app_count=Count("application"))
        .order_by("-posted_at")
    )
    if status_filter:
        qs = qs.filter(status=status_filter)
    return qs


def get_applications_hub(employer_profile, job_id=None, status=None, min_match=None):
    qs = (
        Application.objects.filter(job__employer=employer_profile)
        .exclude(status="Withdrawn")
        .select_related("user", "job", "match_score", "parsed_resume")
        .prefetch_related("timeline_events", "interviews")
        .order_by(F("match_score__overall_score").desc(nulls_last=True), "-applied_at")
    )
    if job_id:
        qs = qs.filter(job_id=job_id)
    if status:
        qs = qs.filter(status=status)
    if min_match:
        qs = qs.filter(match_score__overall_score__gte=float(min_match))
    return qs


def get_employer_interviews(employer_profile, status_filter=None):
    qs = Interview.objects.filter(
        application__job__employer=employer_profile
    ).select_related("application__user", "application__job", "scheduled_by")
    if status_filter:
        qs = qs.filter(status=status_filter)
    return qs.order_by("-scheduled_time")


def get_analytics(employer_profile):
    from django.db.models.functions import TruncMonth

    return {
        "jobs_per_month": (
            Job.objects.filter(employer=employer_profile)
            .annotate(month=TruncMonth("posted_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        ),
        "applications_per_job": (
            Application.objects.filter(job__employer=employer_profile)
            .values("job__id", "job__title")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        ),
        "applications_per_category": (
            Application.objects.filter(job__employer=employer_profile)
            .values("job__category")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        ),
        "pipeline_counts": (
            Application.objects.filter(job__employer=employer_profile)
            .exclude(status="Withdrawn")
            .values("status")
            .annotate(total=Count("id"))
            .order_by("-total")
        ),
    }
