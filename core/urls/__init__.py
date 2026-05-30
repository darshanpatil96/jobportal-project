"""
ARTISAN. URL Configuration — Split Architecture

Routes are organized into four domains:
  - public.py    → Home, about, companies (no auth required)
  - auth.py      → Login, register, activate, verify, password reset
  - candidate.py → Job browsing, applications, profile, dashboard
  - employer.py  → ATS dashboard, jobs CRUD, candidates, interviews, analytics

All URL names are preserved for backward compatibility.
Legacy routes redirect to the new canonical paths.
"""

from django.urls import include, path

from . import public, auth, candidate, employer, legacy

urlpatterns = [
    # ── Public (no auth) ─────────────────────────────────────────────
    path("", include(public.urlpatterns)),

    # ── Shared Auth ──────────────────────────────────────────────────
    path("", include(auth.urlpatterns)),

    # ── Candidate Portal ─────────────────────────────────────────────
    path("", include(candidate.urlpatterns)),

    # ── Employer ATS Workspace ───────────────────────────────────────
    path("employer/", include(employer.urlpatterns)),

    # ── Legacy redirects (backward compatibility) ────────────────────
    path("", include(legacy.urlpatterns)),
]
