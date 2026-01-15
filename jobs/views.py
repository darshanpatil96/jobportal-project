from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Max
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from django.utils.timezone import now
from datetime import timedelta
from .forms import JobForm
from .models import Job, SavedJob
from applications.models import Application
from applications.forms import ApplicationForm
from django.contrib import messages


# 🏠 JOBSEEKER DASHBOARD
@login_required
def jobseeker_dashboard(request):
    """
    Unified jobseeker dashboard showing:
    - Recent recommended jobs (based on applied categories/job_types)
    - My Applications
    - Saved Jobs
    """
    # Block employers from accessing this
    if hasattr(request.user, "userprofile") and request.user.userprofile.role == "employer":
        return redirect("employer_dashboard")
    
    # Get user's recently applied job categories and types for recommendations
    applied_jobs = Application.objects.filter(user=request.user).select_related("job").values_list("job__category", "job__job_type").distinct()
    
    categories = set(cat for cat, _ in applied_jobs if cat)
    job_types = set(jt for _, jt in applied_jobs if jt)
    
    # Get recommended jobs based on applied categories/job_types
    recommended_jobs = Job.objects.filter(status="Open").order_by("-posted_at")
    
    if categories or job_types:
        recommended_jobs = recommended_jobs.filter(
            Q(category__in=categories) | Q(job_type__in=job_types)
        ).exclude(
            application__user=request.user  # Exclude already applied
        )[:5]
    else:
        # If no applications yet, show latest jobs
        recommended_jobs = recommended_jobs[:5]
    
    # Get user's applications
    user_applications = Application.objects.filter(
        user=request.user
    ).select_related("job").order_by("-applied_at")[:5]
    
    # Get user's saved jobs
    user_saved_jobs = SavedJob.objects.filter(
        user=request.user
    ).select_related("job").order_by("-created_at")[:5]
    
    # Get total stats
    total_applications = Application.objects.filter(user=request.user).count()
    total_saved = SavedJob.objects.filter(user=request.user).count()
    
    context = {
        "recommended_jobs": recommended_jobs,
        "user_applications": user_applications,
        "user_saved_jobs": user_saved_jobs,
        "total_applications": total_applications,
        "total_saved": total_saved,
    }
    return render(request, "jobseeker_dashboard.html", context)


# 1️⃣ LIST + SEARCH JOBS
def job_list(request):
    q = request.GET.get("q", "").strip()
    location = request.GET.get("location", "").strip()
    category = request.GET.get("category", "").strip()
    job_type = request.GET.get("job_type", "").strip()

    # Sort & Filter params
    sort = request.GET.get("sort", "newest")
    remote_only = request.GET.get("remote_only")
    internships_only = request.GET.get("internships_only")
    entry_level_only = request.GET.get("entry_level_only")

    jobs = Job.objects.filter(status="Open")

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q)
            | Q(company__icontains=q)
            | Q(description__icontains=q)
            | Q(category__icontains=q)
        )

    if location:
        jobs = jobs.filter(location__icontains=location)

    if category:
        jobs = jobs.filter(category__icontains=category)

    if job_type:
        jobs = jobs.filter(job_type__iexact=job_type)
        
    # Quick Filters
    if remote_only:
        jobs = jobs.filter(job_type="Remote")
        
    if internships_only:
        jobs = jobs.filter(job_type="Internship")
        
    if entry_level_only:
        # Heuristic for entry-level / fresher
        jobs = jobs.filter(
            Q(category__icontains="Fresher") 
            | Q(title__icontains="Fresher") 
            | Q(title__icontains="Junior") 
            | Q(title__icontains="Entry")
            | Q(description__icontains="Entry level")
        )

    # Sorting
    if sort == "salary":
        jobs = jobs.order_by("-salary")
    elif sort == "applications":
        jobs = jobs.annotate(app_count=Count("application")).order_by("-app_count")
    else:
        # Default: newest
        jobs = jobs.order_by("-posted_at")

    # Annotate all jobs with application count
    jobs = jobs.annotate(app_count=Count("application"))
    
    paginator = Paginator(jobs, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    saved_job_ids = set()
    applied_job_ids = set()
    user_is_employer = False
    
    if request.user.is_authenticated and hasattr(request.user, "userprofile"):
        user_is_employer = request.user.userprofile.role == "employer"
        
        if not user_is_employer:
            # For jobseekers: get saved jobs and applied jobs
            saved_job_ids = set(
                SavedJob.objects.filter(user=request.user, job__in=page_obj)
                .values_list("job_id", flat=True)
            )
            applied_job_ids = set(
                Application.objects.filter(user=request.user, job__in=page_obj)
                .values_list("job_id", flat=True)
            )

    context = {
        "page_obj": page_obj,
        "saved_job_ids": saved_job_ids,
        "applied_job_ids": applied_job_ids,
        "user_is_employer": user_is_employer,
        "q": q,
        "location": location,
        "category": category,
        "job_type": job_type,
        "sort": sort,
        "remote_only": remote_only,
        "internships_only": internships_only,
        "entry_level_only": entry_level_only,
    }
    return render(request, "job_list.html", context)


# 2️⃣ JOB DETAIL VIEW
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    applied = False
    is_saved = False
    if request.user.is_authenticated:
        applied = Application.objects.filter(user=request.user, job=job).exists()
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()

    return render(request, "job_detail.html", {
        "job": job,
        "applied": applied,
        "is_saved": is_saved,
    })


# 3️⃣ APPLY TO A JOB
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Block if email not verified
    if not hasattr(request.user, "userprofile") or not request.user.userprofile.email_verified:
        messages.warning(request, "Please verify your email before applying to jobs.")
        return redirect("profile")

    existing = Application.objects.filter(user=request.user, job=job).first()
    if existing:
        messages.info(request, "You have already applied to this job.")
        return redirect("job_detail", job_id=job.id)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.job = job
            app.status = "Applied"
            app.save()
            messages.success(request, "Application submitted.")
            return redirect("job_detail", job_id=job.id)
    else:
        form = ApplicationForm()

    return render(request, "apply_job.html", {"form": form, "job": job})


# 4️⃣ EMPLOYER DASHBOARD
@login_required
def employer_dashboard(request):
    """
    Enhanced employer dashboard with:
    - Active jobs section
    - Closed jobs section
    - Stats per job
    - Basic analytics (jobs per month, applications per job, applications per category)
    """
    # Only employers can view this dashboard
    if not hasattr(request.user, "userprofile") or request.user.userprofile.role != "employer":
        return redirect("job_list")

    employer_profile = request.user.userprofile

    # Get active and closed jobs
    active_jobs = (
        Job.objects
        .filter(employer=employer_profile, status="Open")
        .annotate(app_count=Count("application"))
        .order_by("-posted_at")
    )
    
    closed_jobs = (
        Job.objects
        .filter(employer=employer_profile, status="Closed")
        .annotate(app_count=Count("application"))
        .order_by("-posted_at")
    )
    
    draft_jobs = (
        Job.objects
        .filter(employer=employer_profile, status="Draft")
        .annotate(app_count=Count("application"))
        .order_by("-posted_at")
    )
    
    # Calculate overall stats
    total_jobs = Job.objects.filter(employer=employer_profile).count()
    total_applications = Application.objects.filter(job__employer=employer_profile).count()
    total_views = active_jobs.count()  # We can expand this if we add view tracking

    # --- Basic analytics ---

    # 1) Jobs posted per month (for this employer)
    jobs_per_month = (
        Job.objects
        .filter(employer=employer_profile)
        .annotate(month=TruncMonth("posted_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    # 2) Applications per job (for this employer's jobs)
    applications_per_job = (
        Application.objects
        .filter(job__employer=employer_profile)
        .values("job__id", "job__title")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    # 3) Applications per category (for this employer's jobs)
    applications_per_category = (
        Application.objects
        .filter(job__employer=employer_profile)
        .values("job__category")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return render(request, "employer_dashboard.html", {
        "active_jobs": active_jobs,
        "closed_jobs": closed_jobs,
        "draft_jobs": draft_jobs,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "total_views": total_views,
        "jobs_per_month": jobs_per_month,
        "applications_per_job": applications_per_job,
        "applications_per_category": applications_per_category,
    })


@login_required
@login_required
@login_required
def job_applications(request, job_id):
    # Ensure user is employer
    if not hasattr(request.user, "userprofile") or request.user.userprofile.role != "employer":
        return redirect("job_list")

    job = get_object_or_404(Job, id=job_id, employer=request.user.userprofile)

    if request.method == "POST":
        app_id = request.POST.get("application_id")
        new_status = request.POST.get("status")

        if app_id and new_status:
            application = get_object_or_404(Application, id=app_id, job=job)
            application.status = new_status
            application.save()
            messages.success(
                request,
                f"Status updated to '{new_status}' for {application.user.username}.",
            )

        return redirect("job_applications", job_id=job.id)

    # Employer's active list – hide withdrawn applications
    applications = (
        Application.objects
        .filter(job=job)
        .exclude(status="Withdrawn")
        .select_related("user")
    )

    status_choices_for_employer = [
        (value, label)
        for value, label in Application.STATUS_CHOICES
        if value != "Withdrawn"
    ]

    context = {
        "job": job,
        "applications": applications,
        "STATUS_CHOICES": status_choices_for_employer,
    }
    return render(request, "employer/job_applications.html", context)


@login_required
def create_job(request):
    # Only employers can post jobs
    if not hasattr(request.user, "userprofile") or request.user.userprofile.role != "employer":
        return redirect("job_list")

    if not request.user.userprofile.email_verified:
        messages.warning(request, "Please verify your email before posting jobs.")
        return redirect("profile")

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user.userprofile  # set employer automatically
            job.save()
            return redirect("job_detail", job_id=job.id)
    else:
        form = JobForm()

    return render(request, "job_create.html", {"form": form})


@login_required
def edit_job(request, job_id):
    if not hasattr(request.user, "userprofile") or request.user.userprofile.role != "employer":
        return redirect("job_list")

    job = get_object_or_404(Job, id=job_id, employer=request.user.userprofile)

    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated.")
            return redirect("job_detail", job_id=job.id)
    else:
        form = JobForm(instance=job)

    return render(request, "job_edit.html", {"form": form, "job": job})


@login_required
def delete_job(request, job_id):
    if not hasattr(request.user, "userprofile") or request.user.userprofile.role != "employer":
        return redirect("job_list")

    job = get_object_or_404(Job, id=job_id, employer=request.user.userprofile)

    if request.method == "POST":
        job.delete()
        messages.info(request, "Job deleted.")
        return redirect("employer_dashboard")

    return render(request, "job_confirm_delete.html", {"job": job})


# HOME PAGE VIEW
def home(request):
    latest_jobs = Job.objects.order_by("-posted_at")[:6]
    categories = (
        Job.objects.values_list("category", flat=True)
        .distinct()
        .order_by("category")[:8]
    )
    job_types = [c[0] for c in Job._meta.get_field("job_type").choices]
    return render(request, "home.html", {
        "now": now(),
        "latest_jobs": latest_jobs,
        "categories": categories,
        "job_types": job_types,
    })


from accounts.models import UserProfile

def companies(request):
    employers = (
        UserProfile.objects
        .filter(role="employer")
        .exclude(company_name="")
        .order_by("company_name")
    )
    return render(request, "companies.html", {"employers": employers})


def company_detail(request, company_id):
    company = get_object_or_404(UserProfile, id=company_id, role="employer")
    jobs = Job.objects.filter(employer=company, status="Open").order_by("-posted_at")
    return render(request, "company_detail.html", {"company": company, "jobs": jobs})


def about(request):
    return render(request, "about.html")


@login_required
def my_applications(request):
    """
    Show applications submitted by the logged-in user, with simple sorting.
    """
    sort = request.GET.get("sort", "recent")

    applications = (
        Application.objects
        .filter(user=request.user)
        .select_related("job")
    )

    if sort == "status":
        applications = applications.order_by("status", "-applied_at")
    else:  # default: most recent
        applications = applications.order_by("-applied_at")

    context = {
        "applications": applications,
        "sort": sort,
    }
    return render(request, "my_applications.html", context)


@login_required
def toggle_save_job(request, job_id):
    """
    Toggle saved/unsaved for a job for the current user.
    """
    job = get_object_or_404(Job, id=job_id, status="Open")

    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        # It was already saved → unsave
        saved.delete()
        messages.info(request, "Job removed from your saved list.")
    else:
        messages.success(request, "Job saved to your list.")

    # redirect back to where the user came from
    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or request.META.get("HTTP_REFERER")
        or reverse("job_list")
    )
    return redirect(next_url)


@login_required
def saved_jobs(request):
    """
    List of jobs saved by the current user.
    """
    saved_jobs_qs = (
        SavedJob.objects
        .filter(user=request.user)
        .select_related("job")
        .order_by("-created_at")
    )
    return render(request, "saved_jobs.html", {"saved_jobs": saved_jobs_qs})


# 3.3 Edit & Withdraw Applications

EDIT_WINDOW_HOURS = 24  # you can change this


@login_required
def edit_application(request, app_id):
    """
    Allow a candidate to edit their own application within a time window.
    """
    app = get_object_or_404(Application, id=app_id, user=request.user)

    # Disallow editing after window or if final status
    if app.applied_at < now() - timedelta(hours=EDIT_WINDOW_HOURS) or app.status in [
        "Rejected",
        "Hired",
        "Withdrawn",
    ]:
        messages.info(request, "This application can no longer be edited.")
        return redirect("my_applications")

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES, instance=app)
        if form.is_valid():
            form.save()
            messages.success(request, "Application updated.")
            return redirect("my_applications")
    else:
        form = ApplicationForm(instance=app)

    return render(request, "applications/application_edit.html", {"form": form, "application": app})


@login_required
def withdraw_application(request, app_id):
    """
    Allow a candidate to withdraw their own application within a time window.
    """
    app = get_object_or_404(Application, id=app_id, user=request.user)

    if app.applied_at < now() - timedelta(hours=EDIT_WINDOW_HOURS) or app.status in [
        "Rejected",
        "Hired",
        "Withdrawn",
    ]:
        messages.info(request, "This application can no longer be withdrawn.")
        return redirect("my_applications")

    if request.method == "POST":
        app.status = "Withdrawn"
        app.save()
        messages.info(request, "Application withdrawn.")
        return redirect("my_applications")

    return render(request, "applications/application_confirm_withdraw.html", {"application": app})
