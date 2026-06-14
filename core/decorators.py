"""
Role-based view decorators for ARTISAN platform.

These decorators enforce access control at the view level:
  - @employer_required  → Only employers can access
  - @candidate_required → Only job seekers can access

Usage:
    @login_required
    @employer_required
    def employer_dashboard(request):
        ...

    @login_required
    @candidate_required
    def my_applications(request):
        ...
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from core.services import is_employer, is_jobseeker


def employer_required(view_func):
    """
    Restrict view to authenticated employers.

    Redirect behavior:
      - Not authenticated → login page (with ?next=)
      - Authenticated jobseeker → jobseeker dashboard
      - No profile → home
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse("login")
            return redirect(f"{login_url}?next={request.path}")
        if not is_employer(request.user):
            messages.error(request, "This area is for employers only.")
            if is_jobseeker(request.user):
                return redirect("jobseeker_dashboard")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return wrapper


def candidate_required(view_func):
    """
    Restrict view to authenticated job seekers.

    Redirect behavior:
      - Not authenticated → login page (with ?next=)
      - Authenticated employer → employer dashboard
      - No profile → home
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse("login")
            return redirect(f"{login_url}?next={request.path}")
        if not is_jobseeker(request.user):
            messages.error(request, "This area is for job seekers only.")
            if is_employer(request.user):
                return redirect("employer_dashboard")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return wrapper

