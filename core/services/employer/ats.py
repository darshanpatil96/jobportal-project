"""
ATS (Applicant Tracking System) service helpers for employers.

Thin wrappers and utilities that complement core.hiring.* services.
The core.hiring package owns the business logic; this module provides
view-layer conveniences specific to the employer portal.
"""

from core.hiring.pipeline import PipelineService


def get_pipeline_summary(employer_profile):
    """
    Get a summary of the hiring pipeline for an employer.
    Returns dict of status → count for active applications.
    """
    from django.db.models import Count
    from core.models import Application

    return dict(
        Application.objects.filter(job__employer=employer_profile)
        .exclude(status="Withdrawn")
        .values_list("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )


def get_allowed_transitions(application):
    """Get allowed next statuses for a given application."""
    return PipelineService.get_allowed_next_statuses(application.status)
