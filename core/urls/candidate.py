"""
Candidate portal routes — job browsing, applications, profile, dashboard.

Current paths preserved at /jobs/* and /accounts/profile/* for backward compat.
Future migration: move to /candidate/* prefix.
"""

from django.urls import path

from core import views

urlpatterns = [
    # ── Profile ──────────────────────────────────────────────────────
    path("accounts/profile/", views.profile_detail, name="profile"),
    path("accounts/profile/edit/", views.profile_edit, name="profile_edit"),

    # ── Job browsing ─────────────────────────────────────────────────
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:job_id>/apply/", views.apply_job, name="apply_job"),
    path("jobs/<int:job_id>/save/", views.toggle_save_job, name="toggle_save_job"),
    path("jobs/saved/", views.saved_jobs, name="saved_jobs"),

    # ── Applications ─────────────────────────────────────────────────
    path("jobs/applications/", views.my_applications, name="my_applications"),
    path(
        "jobs/applications/<int:app_id>/edit/",
        views.edit_application,
        name="edit_application",
    ),
    path(
        "jobs/applications/<int:app_id>/withdraw/",
        views.withdraw_application,
        name="withdraw_application",
    ),
    path(
        "jobs/applications/<int:app_id>/timeline/",
        views.application_timeline,
        name="application_timeline",
    ),

    # ── Dashboard ────────────────────────────────────────────────────
    path("dashboard/", views.jobseeker_dashboard, name="jobseeker_dashboard"),
]
