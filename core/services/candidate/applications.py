"""
Application management services for candidates.

Business rules for editing, withdrawing, and validating applications.
"""

from datetime import timedelta

from django.utils import timezone

from core.models import Application


def can_edit_application(application, user):
    """
    Check if a candidate can still edit/withdraw their application.

    Rules:
    - Must be the application owner
    - Cannot edit terminal statuses (Hired, Rejected, Withdrawn)
    - Can only edit within 24 hours of applying
    """
    if application.user != user:
        return False
    terminal = getattr(
        Application, "TERMINAL_STATUSES", {"Rejected", "Hired", "Withdrawn"}
    )
    if application.status in terminal:
        return False
    return application.applied_at >= timezone.now() - timedelta(hours=24)
