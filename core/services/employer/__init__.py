"""
Employer domain services — ATS queries, analytics.

Note: The heavy-lifting employer services already live in core.hiring/:
  - core.hiring.pipeline      → Status transitions
  - core.hiring.workflow      → Application processing orchestration
  - core.hiring.interviews    → Interview scheduling
  - core.hiring.timeline      → Audit log
  - core.hiring.notifications → In-app notifications
  - core.hiring.employer_queries → Dashboard/hub queries

This package provides additional employer-specific helpers
that don't fit into the hiring pipeline domain.
"""
