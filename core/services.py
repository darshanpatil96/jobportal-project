from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import Job, Application, SavedJob, UserProfile


def get_job_filters(request):
    return {
        "q": request.GET.get("q", "").strip(),
        "location": request.GET.get("location", "").strip(),
        "category": request.GET.get("category", "").strip(),
        "job_types": request.GET.getlist("job_type"),
        "salary_range": request.GET.get("salary_range", "").strip(),
        "sort": request.GET.get("sort", "newest"),
        "remote_only": request.GET.get("remote_only"),
        "internships_only": request.GET.get("internships_only"),
        "entry_level_only": request.GET.get("entry_level_only"),
    }


def filter_jobs(jobs, filters):
    q = filters.get("q")
    location = filters.get("location")
    category = filters.get("category")
    job_types = filters.get("job_types")
    remote_only = filters.get("remote_only")
    internships_only = filters.get("internships_only")
    entry_level_only = filters.get("entry_level_only")
    sort = filters.get("sort", "newest")

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q)
            | Q(company__icontains=q)
            | Q(description__icontains=q)
            | Q(category__icontains=q)
        )

    if location:
        jobs = jobs.filter(location__icontains=location)

    if category:
        jobs = jobs.filter(category__icontains=category)

    if job_types:
        jobs = jobs.filter(job_type__in=job_types)

    if remote_only:
        jobs = jobs.filter(job_type="Remote")

    if internships_only:
        jobs = jobs.filter(job_type="Internship")

    if entry_level_only:
        jobs = jobs.filter(
            Q(category__icontains="Fresher")
            | Q(title__icontains="Fresher")
            | Q(title__icontains="Junior")
            | Q(title__icontains="Entry")
            | Q(description__icontains="Entry level")
        )

    if sort == "salary":
        jobs = jobs.order_by("-salary")
    elif sort == "applications":
        jobs = jobs.annotate(app_count=Count("application")).order_by("-app_count")
    else:
        jobs = jobs.order_by("-posted_at")

    return jobs


def get_job_context(user, page_obj):
    saved_job_ids = set()
    applied_job_ids = set()
    user_is_employer = False

    if user.is_authenticated and hasattr(user, "userprofile"):
        user_is_employer = user.userprofile.role == "employer"
        if not user_is_employer:
            saved_job_ids = set(
                SavedJob.objects.filter(user=user, job__in=page_obj).values_list(
                    "job_id", flat=True
                )
            )
            applied_job_ids = set(
                Application.objects.filter(user=user, job__in=page_obj).values_list(
                    "job_id", flat=True
                )
            )

    return saved_job_ids, applied_job_ids, user_is_employer


def get_categories():
    return list(
        Job.objects.filter(status="Open")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )


def is_employer(user):
    return hasattr(user, "userprofile") and user.userprofile.role == "employer"


def is_jobseeker(user):
    return hasattr(user, "userprofile") and user.userprofile.role == "jobseeker"


def can_edit_application(application, user):
    if application.user != user:
        return False
    if application.status in ["Rejected", "Hired", "Withdrawn"]:
        return False
    return application.applied_at >= timezone.now() - timedelta(hours=24)
