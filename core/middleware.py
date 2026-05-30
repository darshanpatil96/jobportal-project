"""
Role-based middleware for ARTISAN platform.

Enforces portal boundaries:
- Employers accessing /candidate/* → redirected to employer dashboard
- Candidates accessing /employer/* → redirected to candidate dashboard
- Unauthenticated users accessing protected routes → redirected to login

This middleware runs AFTER Django's AuthenticationMiddleware.
"""

from django.shortcuts import redirect
from django.urls import reverse


class RoleBasedAccessMiddleware:
    """
    Enforce role-based route access at the middleware level.

    This provides a safety net beyond decorators — even if a decorator
    is accidentally omitted, the middleware catches unauthorized access.

    Protected prefixes:
      /employer/*  → requires employer role
      /dashboard/  → requires jobseeker role (redirects employers)

    Excluded from checks:
      /admin/*     → Django admin handles its own auth
      /api/*       → DRF permissions handle API auth
      /accounts/*  → Shared auth routes (login, register, etc.)
      /static/*    → Static files
      /media/*     → Media files
    """

    EMPLOYER_PREFIX = "/employer/"
    CANDIDATE_DASHBOARD_PREFIX = "/dashboard/"

    EXCLUDED_PREFIXES = (
        "/admin/",
        "/api/",
        "/accounts/",
        "/static/",
        "/media/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip excluded paths
        path = request.path
        if any(path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
            return self.get_response(request)

        # Skip public routes (no auth needed)
        if path in ("/", "/about/", "/jobs/") or path.startswith("/companies/"):
            return self.get_response(request)

        # Skip job detail/browsing (public)
        if path.startswith("/jobs/") and not any(
            seg in path for seg in ["/apply/", "/save/", "/applications/", "/saved/"]
        ):
            return self.get_response(request)

        user = request.user

        # Not authenticated — let Django's login_required handle it
        if not user.is_authenticated:
            return self.get_response(request)

        # Get user role
        profile = getattr(user, "userprofile", None)
        if not profile:
            return self.get_response(request)

        role = profile.role

        # Employer trying to access candidate dashboard
        if path.startswith(self.CANDIDATE_DASHBOARD_PREFIX) and role == "employer":
            return redirect("employer_dashboard")

        # Candidate trying to access employer portal
        if path.startswith(self.EMPLOYER_PREFIX) and role == "jobseeker":
            from django.contrib import messages
            messages.error(request, "This area is for employers only.")
            return redirect("jobseeker_dashboard")

        return self.get_response(request)
