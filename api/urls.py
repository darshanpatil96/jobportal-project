"""
ARTISAN. API URL Configuration

All API endpoints are versioned under /api/v1/
Separated by domain: auth, candidate, employer.
"""

from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # ── Authentication ────────────────────────────────────────────────
    path("v1/auth/token/", TokenObtainPairView.as_view(), name="api_token_obtain"),
    path("v1/auth/token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
    path("v1/auth/", include("api.shared.urls")),

    # ── Candidate API ─────────────────────────────────────────────────
    path("v1/candidate/", include("api.candidate.urls")),

    # ── Employer API ──────────────────────────────────────────────────
    path("v1/employer/", include("api.employer.urls")),
]
