"""
Candidate portal views — job browsing, applications, profile, dashboard.

All views here serve the job-seeker experience.
Employer users are redirected away from candidate-only actions.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.forms import ApplicationForm, UserProfileForm
from core.models import Application, Job, SavedJob, UserProfile
from core.services import (
    can_edit_application,
    filter_jobs,
    get_categories,
    get_job_context,
    get_job_filters,
    is_employer,
)
from core.hiring.pipeline import PipelineService
from core.hiring.timeline import TimelineService
from core.hiring.workflow import ApplicationWorkflowService


# ── Profile ──────────────────────────────────────────────────────────────────


@login_required
def profile_detail(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, "auth/profile.html", {"profile": profile})


@login_required
def profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=profile)
    return render(request, "auth/profile_edit.html", {"form": form})


# ── Job Browsing ─────────────────────────────────────────────────────────────


def job_list(request):
    filters = get_job_filters(request)
    jobs = Job.objects.filter(status="Open").annotate(app_count=Count("application"))
    jobs = filter_jobs(jobs, filters)

    total_jobs = jobs.count()
    paginator = Paginator(jobs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    saved_job_ids, applied_job_ids, user_is_employer = get_job_context(
        request.user, page_obj
    )
    has_filters = any(
        [
            filters["q"],
            filters["location"],
            filters["category"],
            filters["job_types"],
            filters["remote_only"],
            filters["internships_only"],
            filters["entry_level_only"],
        ]
    )

    job_types = [
        ("Full-Time", "Full-Time"),
        ("Part-Time", "Part-Time"),
        ("Internship", "Internship"),
        ("Remote", "Remote"),
    ]

    return render(
        request,
        "jobs/job_list.html",
        {
            "page_obj": page_obj,
            "saved_job_ids": saved_job_ids,
            "applied_job_ids": applied_job_ids,
            "user_is_employer": user_is_employer,
            "categories": get_categories(),
            "job_types": job_types,
            "total_jobs": total_jobs,
            "has_filters": has_filters,
            **filters,
        },
    )


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applied = is_saved = False
    if request.user.is_authenticated:
        applied = Application.objects.filter(user=request.user, job=job).exists()
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()

    similar_jobs = (
        Job.objects.filter(
            Q(category=job.category) | Q(job_type=job.job_type), status="Open"
        )
        .exclude(id=job.id)
        .order_by("-posted_at")[:4]
    )

    return render(
        request,
        "jobs/job_detail.html",
        {
            "job": job,
            "applied": applied,
            "is_saved": is_saved,
            "similar_jobs": similar_jobs,
            "user_is_employer": is_employer(request.user) if request.user.is_authenticated else False,
        },
    )


# ── Applications ─────────────────────────────────────────────────────────────


@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    profile = getattr(request.user, "userprofile", None)

    # Prevent employers from applying to jobs
    if profile and profile.role == "employer":
        messages.error(
            request,
            "Employers cannot apply for jobs. Switch to a job seeker account to apply.",
        )
        return redirect("job_detail", job_id=job.id)



    if Application.objects.filter(user=request.user, job=job).exists():
        messages.info(request, "You have already applied to this job.")
        return redirect("job_detail", job_id=job.id)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.job = job
            app.status = "Applied"
            app.save()
            ApplicationWorkflowService.process_new_application(app)
            messages.success(
                request,
                "Application submitted. Resume parsing and match scoring completed.",
            )
            return redirect("job_detail", job_id=job.id)
    else:
        form = ApplicationForm()
    return render(request, "jobs/apply.html", {"form": form, "job": job})


@login_required
def toggle_save_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, status="Open")
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        saved.delete()
        messages.info(request, "Job removed from saved list.")
    else:
        messages.success(request, "Job saved.")
    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or request.META.get("HTTP_REFERER")
        or "job_list"
    )
    return redirect(next_url)


@login_required
def saved_jobs(request):
    saved_jobs_qs = (
        SavedJob.objects.filter(user=request.user)
        .select_related("job")
        .order_by("-created_at")
    )
    return render(request, "jobs/saved_jobs.html", {"saved_jobs": saved_jobs_qs})


@login_required
def my_applications(request):
    sort = request.GET.get("sort", "recent")
    applications = Application.objects.filter(user=request.user).select_related("job")
    applications = (
        applications.order_by("status", "-applied_at")
        if sort == "status"
        else applications.order_by("-applied_at")
    )
    return render(
        request,
        "jobs/my_applications.html",
        {"applications": applications, "sort": sort},
    )


@login_required
def edit_application(request, app_id):
    app = get_object_or_404(Application, id=app_id, user=request.user)
    if not can_edit_application(app, request.user):
        messages.info(request, "This application can no longer be edited.")
        return redirect("my_applications")
    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES, instance=app)
        if form.is_valid():
            resume_changed = "resume" in form.changed_data
            form.save()
            if resume_changed:
                ApplicationWorkflowService.reprocess_application(app)
            messages.success(request, "Application updated.")
            return redirect("my_applications")
    else:
        form = ApplicationForm(instance=app)
    return render(
        request, "jobs/application_edit.html", {"form": form, "application": app}
    )


@login_required
def withdraw_application(request, app_id):
    app = get_object_or_404(Application, id=app_id, user=request.user)
    if not can_edit_application(app, request.user):
        messages.info(request, "This application can no longer be withdrawn.")
        return redirect("my_applications")
    if request.method == "POST":
        try:
            PipelineService.transition(
                app, "Withdrawn", updated_by=request.user, notes="Withdrawn by candidate"
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect("my_applications")
        messages.info(request, "Application withdrawn.")
        return redirect("my_applications")
    return render(request, "jobs/application_withdraw.html", {"application": app})


@login_required
def application_timeline(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    is_owner = application.user == request.user
    is_job_employer = (
        is_employer(request.user)
        and application.job.employer == request.user.userprofile
    )
    if not (is_owner or is_job_employer):
        messages.error(request, "You do not have permission to view this timeline.")
        return redirect("home")

    if is_job_employer:
        return redirect("employer_candidate_detail", app_id=application.id)

    events = TimelineService.get_timeline(application)
    history = application.status_history.select_related("updated_by").all()
    interviews = application.interviews.all()
    match_score = getattr(application, "match_score", None)
    parsed = getattr(application, "parsed_resume", None)

    return render(
        request,
        "jobs/application_timeline.html",
        {
            "application": application,
            "events": events,
            "history": history,
            "interviews": interviews,
            "match_score": match_score,
            "parsed_resume": parsed,
            "is_employer_view": is_job_employer,
        },
    )


# ── Dashboard ────────────────────────────────────────────────────────────────


@login_required
def jobseeker_dashboard(request):
    if is_employer(request.user):
        return redirect("employer_dashboard")

    applied_jobs = (
        Application.objects.filter(user=request.user)
        .select_related("job")
        .values_list("job__category", "job__job_type")
        .distinct()
    )
    categories = {cat for cat, _ in applied_jobs if cat}
    job_types = {jt for _, jt in applied_jobs if jt}

    recommended_jobs = Job.objects.filter(status="Open")
    if categories or job_types:
        recommended_jobs = recommended_jobs.filter(
            Q(category__in=categories) | Q(job_type__in=job_types)
        ).exclude(application__user=request.user)[:5]
    else:
        recommended_jobs = recommended_jobs[:5]

    user_applications = (
        Application.objects.filter(user=request.user)
        .select_related("job")
        .order_by("-applied_at")[:5]
    )
    user_saved_jobs = (
        SavedJob.objects.filter(user=request.user)
        .select_related("job")
        .order_by("-created_at")[:5]
    )

    return render(
        request,
        "candidate/dashboard.html",
        {
            "recommended_jobs": recommended_jobs,
            "user_applications": user_applications,
            "user_saved_jobs": user_saved_jobs,
            "total_applications": Application.objects.filter(user=request.user).count(),
            "total_saved": SavedJob.objects.filter(user=request.user).count(),
        },
    )
