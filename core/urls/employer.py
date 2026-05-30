"""
Employer ATS workspace routes — all under /employer/ prefix.

Dashboard, job management, candidate pipeline, interviews, analytics.
All views require @employer_required decorator.
"""

from django.urls import path
from django.views.generic import RedirectView

from core import views_employer

# Note: These are included under path("employer/", ...) in __init__.py
# So the actual URLs are /employer/dashboard/, /employer/jobs/, etc.

urlpatterns = [
    # ── Dashboard ────────────────────────────────────────────────────
    path("", views_employer.employer_dashboard, name="employer_dashboard"),
    path(
        "dashboard/",
        RedirectView.as_view(pattern_name="employer_dashboard", permanent=False),
    ),

    # ── Job Management ───────────────────────────────────────────────
    path("jobs/", views_employer.employer_jobs_list, name="employer_jobs"),
    path("jobs/create/", views_employer.employer_job_create, name="employer_job_create"),
    path("jobs/<int:job_id>/", views_employer.employer_job_detail, name="employer_job_detail"),
    path("jobs/<int:job_id>/edit/", views_employer.employer_job_edit, name="employer_job_edit"),
    path("jobs/<int:job_id>/delete/", views_employer.employer_job_delete, name="employer_job_delete"),

    # ── Candidate Pipeline ───────────────────────────────────────────
    path("applications/", views_employer.employer_applications_hub, name="employer_applications"),
    path("applications/<int:app_id>/", views_employer.employer_candidate_detail, name="employer_candidate_detail"),

    # ── Interviews ───────────────────────────────────────────────────
    path("interviews/", views_employer.employer_interviews_list, name="employer_interviews"),

    # ── Analytics ────────────────────────────────────────────────────
    path("analytics/", views_employer.employer_analytics, name="employer_analytics"),

    # ── Company Profile ──────────────────────────────────────────────
    path("company/", views_employer.employer_company_profile, name="employer_company"),
]
