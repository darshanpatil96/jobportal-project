"""
ARTISAN. services — backward compatibility re-export.

All service functions have been moved to domain-specific modules:
  - core.services.shared.roles        → is_employer, is_jobseeker
  - core.services.candidate.jobs      → get_job_filters, filter_jobs, etc.
  - core.services.candidate.applications → can_edit_application

This file re-exports everything so existing imports still work:
  from core.services import is_employer, filter_jobs, ...
"""

from core.services.shared.roles import is_employer, is_jobseeker  # noqa: F401
from core.services.candidate.jobs import (  # noqa: F401
    get_job_filters,
    filter_jobs,
    get_job_context,
    get_categories,
)
from core.services.candidate.applications import can_edit_application  # noqa: F401
