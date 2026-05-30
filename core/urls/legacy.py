"""
Legacy URL redirects — backward compatibility.

These routes existed before the portal separation and are kept
so old bookmarks, emails, and external links still work.
They redirect to the new canonical employer portal paths.
"""

from django.urls import path

from core import views, views_employer

urlpatterns = [
    # Old employer job management URLs → new employer portal
    path("jobs/create/", views_employer.employer_job_create, name="create_job"),
    path("jobs/<int:job_id>/edit/", views_employer.employer_job_edit, name="edit_job"),
    path("jobs/<int:job_id>/delete/", views_employer.employer_job_delete, name="delete_job"),

    # Old application management URLs → employer portal
    path(
        "jobs/<int:job_id>/applications/",
        views.redirect_job_applications_to_portal,
        name="job_applications",
    ),
    path(
        "jobs/applications/<int:app_id>/interviews/schedule/",
        views.redirect_schedule_interview_to_portal,
        name="schedule_interview",
    ),
    path(
        "jobs/applications/<int:app_id>/interviews/<int:interview_id>/status/",
        views.update_interview_status,
        name="update_interview_status",
    ),
]
