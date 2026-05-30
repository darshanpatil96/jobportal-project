"""
ARTISAN. Service Layer — Domain-Driven Structure

Services are organized by business domain:
  - shared/     → Role checks, auth helpers, notifications
  - candidate/  → Job search, applications, profiles
  - employer/   → ATS queries, analytics (delegates to core.hiring.*)

The core.hiring/ package remains the source of truth for:
  - Pipeline state machine (pipeline.py)
  - Application workflow orchestration (workflow.py)
  - Interview scheduling (interviews.py)
  - Timeline audit log (timeline.py)
  - Notification dispatch (notifications.py)

This __init__.py re-exports all functions from the old services.py
so existing imports (`from core.services import is_employer`) still work.
"""

# ── Shared services (role checks, utilities) ─────────────────────────────────
from core.services.shared.roles import (  # noqa: F401
    is_employer,
    is_jobseeker,
)

# ── Candidate services ───────────────────────────────────────────────────────
from core.services.candidate.jobs import (  # noqa: F401
    get_job_filters,
    filter_jobs,
    get_job_context,
    get_categories,
)
from core.services.candidate.applications import (  # noqa: F401
    can_edit_application,
)
