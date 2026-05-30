"""
ARTISAN. views — re-export layer for backward compatibility.

All view functions have been moved to domain-specific modules:
  - views_public.py    → home, about, companies
  - views_auth.py      → login, register, activate, verify
  - views_candidate.py → jobs, applications, profile, dashboard
  - views_employer.py  → ATS dashboard, pipeline, interviews (unchanged)

This file re-exports everything so existing URL imports
(`from core import views; views.home`) continue working.
"""

# ── Public views ─────────────────────────────────────────────────────────────
from core.views_public import (  # noqa: F401
    home,
    companies,
    company_detail,
    about,
)

# ── Auth views ───────────────────────────────────────────────────────────────
from core.views_auth import (  # noqa: F401
    register_user,
    activate_account,
    login_user,
    logout_user,
    verify_email,
    resend_verification,
    notifications_list,
)

# ── Candidate views ──────────────────────────────────────────────────────────
from core.views_candidate import (  # noqa: F401
    profile_detail,
    profile_edit,
    job_list,
    job_detail,
    apply_job,
    toggle_save_job,
    saved_jobs,
    my_applications,
    edit_application,
    withdraw_application,
    application_timeline,
    jobseeker_dashboard,
)

# ── Legacy redirects (kept here for URL imports) ─────────────────────────────
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from core.hiring.interviews import InterviewService
from core.models import Application, Interview
from core.services import is_employer


@login_required
def redirect_job_applications_to_portal(request, job_id):
    """Legacy URL → employer applications hub filtered by job."""
    if not is_employer(request.user):
        return redirect("job_list")
    return redirect(f"{reverse('employer_applications')}?job={job_id}")


@login_required
def redirect_schedule_interview_to_portal(request, app_id):
    if not is_employer(request.user):
        return redirect("job_list")
    return redirect("employer_candidate_detail", app_id=app_id)


@login_required
def update_interview_status(request, app_id, interview_id):
    if not is_employer(request.user):
        return redirect("job_list")
    application = get_object_or_404(
        Application,
        id=app_id,
        job__employer=request.user.userprofile,
    )
    interview = get_object_or_404(Interview, id=interview_id, application=application)

    if request.method == "POST":
        status = request.POST.get("status") or request.POST.get("interview_status")
        if status:
            InterviewService.update_status(interview, status)
            messages.success(request, "Interview status updated.")
    return redirect("employer_candidate_detail", app_id=application.id)
