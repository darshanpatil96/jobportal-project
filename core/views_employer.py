"""Employer portal views — hiring manager UI under /employer/."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.decorators import employer_required
from core.forms import (
    InterviewScheduleForm,
    InterviewStatusForm,
    JobForm,
    UserProfileForm,
)
from core.hiring.employer_queries import (
    get_analytics,
    get_applications_hub,
    get_employer_interviews,
    get_employer_jobs,
    get_employer_profile,
    get_employer_stats,
    get_recent_applications,
    get_upcoming_interviews,
)
from core.hiring.interviews import InterviewService
from core.hiring.pipeline import PipelineService
from core.hiring.timeline import TimelineService
from core.models import Application, Interview, Job, UserProfile


def _employer_profile_or_404(user):
    return get_object_or_404(UserProfile, user=user, role="employer")


@login_required
@employer_required
def employer_dashboard(request):
    profile = _employer_profile_or_404(request.user)
    stats = get_employer_stats(profile)
    analytics = get_analytics(profile)

    return render(
        request,
        "employer/dashboard_v2.html",
        {
            "profile": profile,
            "stats": stats,
            "recent_applications": get_recent_applications(profile),
            "upcoming_interviews": get_upcoming_interviews(profile),
            "active_jobs": get_employer_jobs(profile, "Open")[:6],
            "pipeline_counts": analytics.get("pipeline_counts"),
        },
    )


@login_required
@employer_required
def employer_jobs_list(request):
    profile = _employer_profile_or_404(request.user)
    status_filter = request.GET.get("status", "")

    return render(
        request,
        "employer/jobs_list.html",
        {
            "profile": profile,
            "status_filter": status_filter,
            "open_jobs": get_employer_jobs(profile, "Open"),
            "closed_jobs": get_employer_jobs(profile, "Closed"),
            "draft_jobs": get_employer_jobs(profile, "Draft"),
        },
    )


@login_required
@employer_required
def employer_job_detail(request, job_id):
    from django.db.models import F

    profile = _employer_profile_or_404(request.user)
    job = get_object_or_404(Job, id=job_id, employer=profile)
    # BUG FIX: same nulls_last fix as the applications hub — without this,
    # newly applied candidates (no match score yet) were pushed past position 10
    # and silently disappeared from the job detail sidebar.
    applications = (
        Application.objects.filter(job=job)
        .exclude(status="Withdrawn")
        .select_related("user", "match_score")
        .order_by(F("match_score__overall_score").desc(nulls_last=True), "-applied_at")[:10]
    )
    return render(
        request,
        "employer/job_detail.html",
        {"profile": profile, "job": job, "applications": applications},
    )


@login_required
@employer_required
def employer_job_create(request):
    profile = _employer_profile_or_404(request.user)

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = profile
            
            # Fetch the workspace for the employer
            from core.services.employer.workspace import WorkspaceService
            workspace = WorkspaceService.get_user_workspace(profile.user)
            if not workspace:
                # Fallback to auto-create if they don't have one
                if not profile.company_name:
                    profile.company_name = f"{profile.user.username} Company"
                    profile.save(update_fields=['company_name'])
                workspace = WorkspaceService.auto_create_from_profile(profile)
            
            job.workspace = workspace
            job.save()
            messages.success(request, "Job posted successfully.")
            return redirect("employer_job_detail", job_id=job.id)
    else:
        form = JobForm()
    return render(
        request,
        "employer/job_form.html",
        {"form": form, "action": "Create", "profile": profile},
    )


@login_required
@employer_required
def employer_job_edit(request, job_id):
    profile = _employer_profile_or_404(request.user)
    job = get_object_or_404(Job, id=job_id, employer=profile)

    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated.")
            return redirect("employer_job_detail", job_id=job.id)
    else:
        form = JobForm(instance=job)
    return render(
        request,
        "employer/job_form.html",
        {"form": form, "job": job, "action": "Edit", "profile": profile},
    )


@login_required
@employer_required
def employer_job_delete(request, job_id):
    profile = _employer_profile_or_404(request.user)
    job = get_object_or_404(Job, id=job_id, employer=profile)

    if request.method == "POST":
        job.delete()
        messages.info(request, "Job deleted.")
        return redirect("employer_jobs")
    return render(
        request,
        "employer/job_confirm_delete.html",
        {"job": job, "profile": profile},
    )


@login_required
@employer_required
def employer_applications_hub(request):
    profile = _employer_profile_or_404(request.user)
    job_id = request.GET.get("job")
    status = request.GET.get("status", "")
    min_match = request.GET.get("min_match")

    applications = get_applications_hub(
        profile,
        job_id=job_id or None,
        status=status or None,
        min_match=min_match or None,
    )
    jobs = Job.objects.filter(employer=profile).order_by("-posted_at")

    return render(
        request,
        "employer/applications_hub.html",
        {
            "profile": profile,
            "applications": applications,
            "jobs": jobs,
            "selected_job": job_id,
            "selected_status": status,
            "selected_min_match": min_match,
            "status_choices": Application.STATUS_CHOICES,
        },
    )


@login_required
@employer_required
def employer_candidate_detail(request, app_id):
    profile = _employer_profile_or_404(request.user)
    application = get_object_or_404(
        Application,
        id=app_id,
        job__employer=profile,
    )

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "status":
            new_status = request.POST.get("status")
            notes = request.POST.get("notes", "")
            if new_status:
                try:
                    PipelineService.transition(
                        application,
                        new_status,
                        updated_by=request.user,
                        notes=notes,
                    )
                    messages.success(request, f"Status updated to {new_status}.")
                except ValidationError as exc:
                    messages.error(request, str(exc))
        elif action == "interview":
            form = InterviewScheduleForm(request.POST)
            if form.is_valid():
                try:
                    InterviewService.schedule(
                        application=application,
                        scheduled_by=request.user,
                        scheduled_time=form.cleaned_data["scheduled_time"],
                        interview_type=form.cleaned_data["interview_type"],
                        meeting_link=form.cleaned_data.get("meeting_link", ""),
                        notes=form.cleaned_data.get("notes", ""),
                    )
                    messages.success(request, "Interview scheduled.")
                except ValidationError as exc:
                    messages.error(request, str(exc))
        elif action == "interview_status":
            interview_id = request.POST.get("interview_id")
            new_status = request.POST.get("interview_status")
            if interview_id and new_status:
                interview = get_object_or_404(
                    Interview, id=interview_id, application=application
                )
                InterviewService.update_status(interview, new_status)
                messages.success(request, "Interview status updated.")
        return redirect("employer_candidate_detail", app_id=application.id)

    application.allowed_status_list = PipelineService.get_allowed_next_statuses(
        application.status
    ) + [application.status]

    return render(
        request,
        "employer/candidate_detail.html",
        {
            "profile": profile,
            "application": application,
            "match_score": getattr(application, "match_score", None),
            "parsed_resume": getattr(application, "parsed_resume", None),
            "events": TimelineService.get_timeline(application),
            "history": application.status_history.select_related("updated_by").all(),
            "interviews": application.interviews.all(),
            "interview_form": InterviewScheduleForm(),
            "pipeline_statuses": Application.STATUS_CHOICES,
        },
    )


@login_required
@employer_required
def employer_interviews_list(request):
    profile = _employer_profile_or_404(request.user)
    status_filter = request.GET.get("status", "")

    return render(
        request,
        "employer/interviews_list.html",
        {
            "profile": profile,
            "status_filter": status_filter,
            "interviews": get_employer_interviews(
                profile, status_filter or None
            ),
            "upcoming": get_upcoming_interviews(profile, limit=20),
        },
    )


@login_required
@employer_required
def employer_analytics(request):
    profile = _employer_profile_or_404(request.user)
    analytics = get_analytics(profile)
    stats = get_employer_stats(profile)

    return render(
        request,
        "employer/analytics.html",
        {"profile": profile, "stats": stats, **analytics},
    )


@login_required
@employer_required
def employer_company_profile(request):
    profile = _employer_profile_or_404(request.user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.role = "employer"
            saved.save()
            messages.success(request, "Company profile updated.")
            return redirect("employer_company")
    else:
        form = UserProfileForm(instance=profile)

    return render(
        request,
        "employer/company_profile.html",
        {"profile": profile, "form": form},
    )


# Legacy redirects
@login_required
@employer_required
def employer_legacy_dashboard_redirect(request):
    return redirect("employer_dashboard")
