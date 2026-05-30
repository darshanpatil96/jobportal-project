"""
Public views — no authentication required.

Home page, about, company directory.
These are shared between both candidate and employer experiences.
"""

from django.shortcuts import get_object_or_404, render

from core.models import Job, UserProfile
from core.services import get_categories


def home(request):
    latest_jobs = Job.objects.filter(status="Open").order_by("-posted_at")[:6]
    categories = get_categories()[:8] or [
        "Software Engineering",
        "Design",
        "Marketing",
        "Sales",
    ]
    companies = list(
        UserProfile.objects.filter(role="employer")
        .exclude(company_name="")
        .order_by("-company_name")[:6]
    )
    return render(
        request,
        "home.html",
        {
            "latest_jobs": latest_jobs,
            "categories": categories,
            "companies": companies,
        },
    )


def companies(request):
    employers = (
        UserProfile.objects.filter(role="employer")
        .exclude(company_name="")
        .order_by("company_name")
    )
    return render(request, "jobs/companies.html", {"employers": employers})


def company_detail(request, company_id):
    company = get_object_or_404(UserProfile, id=company_id, role="employer")
    jobs = Job.objects.filter(employer=company, status="Open").order_by("-posted_at")
    return render(
        request, "jobs/company_detail.html", {"company": company, "jobs": jobs}
    )


def about(request):
    return render(request, "pages/about.html")
