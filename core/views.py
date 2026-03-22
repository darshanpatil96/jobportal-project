from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from .models import Job, Application, SavedJob, UserProfile, Notification
from .models import account_activation_token as token_generator
from .forms import UserRegisterForm, UserProfileForm, JobForm, ApplicationForm
from .services import (
    get_job_filters,
    filter_jobs,
    get_job_context,
    get_categories,
    is_employer,
    can_edit_application,
)
from .utils import decode_uid, send_activation_email


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


def register_user(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_activation_email(request, user)
            login(request, user)
            messages.info(
                request, "Registration successful. We have sent a verification email."
            )
            return redirect("home")
    else:
        form = UserRegisterForm()
    return render(request, "auth/register.html", {"form": form})


def activate_account(request, uidb64, token):
    uid = decode_uid(uidb64)
    try:
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user and token_generator.check_token(user, token):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if not profile.email_verified:
            profile.email_verified = True
            profile.save()
            messages.success(request, "Email verified successfully.")
        return redirect("login")
    messages.error(request, "Activation link is invalid or expired.")
    return redirect("login")


def login_user(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if hasattr(user, "userprofile"):
                return redirect(
                    "employer_dashboard"
                    if user.userprofile.role == "employer"
                    else "jobseeker_dashboard"
                )
            return redirect("job_list")
    else:
        form = AuthenticationForm(request)
    return render(request, "auth/login.html", {"form": form})


@login_required
def profile_detail(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, "auth/profile.html", {"profile": profile})


@login_required
def profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=profile)
    return render(request, "auth/profile_edit.html", {"form": form})


@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "auth/notifications.html", {"notifications": notifications})


def job_list(request):
    filters = get_job_filters(request)
    jobs = Job.objects.filter(status="Open").annotate(app_count=Count("application"))
    jobs = filter_jobs(jobs, filters)

    total_jobs = jobs.count()
    paginator = Paginator(jobs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    saved_job_ids, applied_job_ids, user_is_employer = get_job_context(
        request.user, page_obj
    )
    has_filters = any(
        [
            filters["q"],
            filters["location"],
            filters["category"],
            filters["job_types"],
            filters["remote_only"],
            filters["internships_only"],
            filters["entry_level_only"],
        ]
    )

    job_types = [
        ("Full-Time", "Full-Time"),
        ("Part-Time", "Part-Time"),
        ("Internship", "Internship"),
        ("Remote", "Remote"),
    ]

    return render(
        request,
        "jobs/job_list.html",
        {
            "page_obj": page_obj,
            "saved_job_ids": saved_job_ids,
            "applied_job_ids": applied_job_ids,
            "user_is_employer": user_is_employer,
            "categories": get_categories(),
            "job_types": job_types,
            "total_jobs": total_jobs,
            "has_filters": has_filters,
            **filters,
        },
    )


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applied = is_saved = False
    if request.user.is_authenticated:
        applied = Application.objects.filter(user=request.user, job=job).exists()
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()

    similar_jobs = (
        Job.objects.filter(
            Q(category=job.category) | Q(job_type=job.job_type), status="Open"
        )
        .exclude(id=job.id)
        .order_by("-posted_at")[:4]
    )

    return render(
        request,
        "jobs/job_detail.html",
        {
            "job": job,
            "applied": applied,
            "is_saved": is_saved,
            "similar_jobs": similar_jobs,
        },
    )


@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    profile = getattr(request.user, "userprofile", None)

    if not profile or not profile.email_verified:
        messages.warning(request, "Please verify your email before applying.")
        return redirect("profile")

    if Application.objects.filter(user=request.user, job=job).exists():
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
    return render(request, "jobs/apply.html", {"form": form, "job": job})


@login_required
def toggle_save_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, status="Open")
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        saved.delete()
        messages.info(request, "Job removed from saved list.")
    else:
        messages.success(request, "Job saved.")
    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or request.META.get("HTTP_REFERER")
        or "job_list"
    )
    return redirect(next_url)


@login_required
def saved_jobs(request):
    saved_jobs_qs = (
        SavedJob.objects.filter(user=request.user)
        .select_related("job")
        .order_by("-created_at")
    )
    return render(request, "jobs/saved_jobs.html", {"saved_jobs": saved_jobs_qs})


@login_required
def my_applications(request):
    sort = request.GET.get("sort", "recent")
    applications = Application.objects.filter(user=request.user).select_related("job")
    applications = (
        applications.order_by("status", "-applied_at")
        if sort == "status"
        else applications.order_by("-applied_at")
    )
    return render(
        request,
        "jobs/my_applications.html",
        {"applications": applications, "sort": sort},
    )


@login_required
def edit_application(request, app_id):
    app = get_object_or_404(Application, id=app_id, user=request.user)
    if not can_edit_application(app, request.user):
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
    return render(
        request, "jobs/application_edit.html", {"form": form, "application": app}
    )


@login_required
def withdraw_application(request, app_id):
    app = get_object_or_404(Application, id=app_id, user=request.user)
    if not can_edit_application(app, request.user):
        messages.info(request, "This application can no longer be withdrawn.")
        return redirect("my_applications")
    if request.method == "POST":
        app.status = "Withdrawn"
        app.save()
        messages.info(request, "Application withdrawn.")
        return redirect("my_applications")
    return render(request, "jobs/application_withdraw.html", {"application": app})


@login_required
def jobseeker_dashboard(request):
    if is_employer(request.user):
        return redirect("employer_dashboard")

    applied_jobs = (
        Application.objects.filter(user=request.user)
        .select_related("job")
        .values_list("job__category", "job__job_type")
        .distinct()
    )
    categories = {cat for cat, _ in applied_jobs if cat}
    job_types = {jt for _, jt in applied_jobs if jt}

    recommended_jobs = Job.objects.filter(status="Open")
    if categories or job_types:
        recommended_jobs = recommended_jobs.filter(
            Q(category__in=categories) | Q(job_type__in=job_types)
        ).exclude(application__user=request.user)[:5]
    else:
        recommended_jobs = recommended_jobs[:5]

    user_applications = (
        Application.objects.filter(user=request.user)
        .select_related("job")
        .order_by("-applied_at")[:5]
    )
    user_saved_jobs = (
        SavedJob.objects.filter(user=request.user)
        .select_related("job")
        .order_by("-created_at")[:5]
    )

    return render(
        request,
        "dashboard/jobseeker.html",
        {
            "recommended_jobs": recommended_jobs,
            "user_applications": user_applications,
            "user_saved_jobs": user_saved_jobs,
            "total_applications": Application.objects.filter(user=request.user).count(),
            "total_saved": SavedJob.objects.filter(user=request.user).count(),
        },
    )


@login_required
def employer_dashboard(request):
    if not is_employer(request.user):
        return redirect("job_list")

    employer_profile = request.user.userprofile
    active_jobs = (
        Job.objects.filter(employer=employer_profile, status="Open")
        .annotate(app_count=Count("application"))
        .order_by("-posted_at")
    )
    closed_jobs = (
        Job.objects.filter(employer=employer_profile, status="Closed")
        .annotate(app_count=Count("application"))
        .order_by("-posted_at")
    )
    draft_jobs = (
        Job.objects.filter(employer=employer_profile, status="Draft")
        .annotate(app_count=Count("application"))
        .order_by("-posted_at")
    )

    total_jobs = Job.objects.filter(employer=employer_profile).count()
    total_applications = Application.objects.filter(
        job__employer=employer_profile
    ).count()

    jobs_per_month = (
        Job.objects.filter(employer=employer_profile)
        .annotate(month=TruncMonth("posted_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    applications_per_job = (
        Application.objects.filter(job__employer=employer_profile)
        .values("job__id", "job__title")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    applications_per_category = (
        Application.objects.filter(job__employer=employer_profile)
        .values("job__category")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return render(
        request,
        "dashboard/employer.html",
        {
            "active_jobs": active_jobs,
            "closed_jobs": closed_jobs,
            "draft_jobs": draft_jobs,
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "jobs_per_month": jobs_per_month,
            "applications_per_job": applications_per_job,
            "applications_per_category": applications_per_category,
        },
    )


@login_required
def job_applications(request, job_id):
    if not is_employer(request.user):
        return redirect("job_list")
    job = get_object_or_404(Job, id=job_id, employer=request.user.userprofile)

    if request.method == "POST":
        app_id = request.POST.get("application_id")
        new_status = request.POST.get("status")
        if app_id and new_status:
            application = get_object_or_404(Application, id=app_id, job=job)
            application.status = new_status
            application.save()
            messages.success(request, f"Status updated to '{new_status}'.")

    applications = (
        Application.objects.filter(job=job)
        .exclude(status="Withdrawn")
        .select_related("user")
    )
    status_choices = [(v, l) for v, l in Application.STATUS_CHOICES if v != "Withdrawn"]

    return render(
        request,
        "dashboard/job_applications.html",
        {
            "job": job,
            "applications": applications,
            "STATUS_CHOICES": status_choices,
        },
    )


@login_required
def create_job(request):
    if not is_employer(request.user):
        return redirect("job_list")
    if not request.user.userprofile.email_verified:
        messages.warning(request, "Please verify your email before posting jobs.")
        return redirect("profile")

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user.userprofile
            job.save()
            return redirect("job_detail", job_id=job.id)
    else:
        form = JobForm()
    return render(request, "jobs/job_form.html", {"form": form, "action": "Create"})


@login_required
def edit_job(request, job_id):
    if not is_employer(request.user):
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
    return render(
        request, "jobs/job_form.html", {"form": form, "job": job, "action": "Edit"}
    )


@login_required
def delete_job(request, job_id):
    if not is_employer(request.user):
        return redirect("job_list")
    job = get_object_or_404(Job, id=job_id, employer=request.user.userprofile)

    if request.method == "POST":
        job.delete()
        messages.info(request, "Job deleted.")
        return redirect("employer_dashboard")
    return render(request, "jobs/job_confirm_delete.html", {"job": job})


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
