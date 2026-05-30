"""
Shared authentication views — used by both candidates and employers.

Contains: login, logout, register, email activation, verification.
No role-specific logic beyond the post-login redirect.
"""

from django.contrib import messages
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse

from core.forms import UserRegisterForm
from core.models import UserProfile, account_activation_token as token_generator
from core.utils import build_activation_link, decode_uid, send_activation_email


def register_user(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            activation_link = send_activation_email(request, user)
            login(request, user)
            messages.info(
                request,
                "Registration successful. Check your email to verify before applying.",
            )
            from django.conf import settings as django_settings

            if django_settings.DEBUG:
                messages.warning(
                    request,
                    f"DEV: Open this link to verify your email: {activation_link}",
                )
            return redirect("verify_email")
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
        login(request, user)
        messages.success(request, "Email verified! You can now apply for jobs.")
        next_url = request.GET.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect("job_list")
    messages.error(request, "Activation link is invalid or expired.")
    return redirect("verify_email")


def login_user(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Honor ?next= parameter first
            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)

            # Role-based redirect
            if hasattr(user, "userprofile"):
                if user.userprofile.role == "employer":
                    return redirect("employer_dashboard")
                else:
                    return redirect("jobseeker_dashboard")
            return redirect("job_list")
    else:
        form = AuthenticationForm(request)
    return render(request, "auth/login.html", {"form": form})


def logout_user(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("home")


@login_required
def verify_email(request):
    """Prompt unverified users to confirm email before applying/posting jobs."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.email_verified:
        next_url = request.GET.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect("profile")

    from django.conf import settings as django_settings

    next_path = request.GET.get("next", "")
    activation_link = None
    if django_settings.DEBUG:
        activation_link = build_activation_link(request, request.user, next_path)

    return render(
        request,
        "auth/verify_email.html",
        {
            "profile": profile,
            "next": next_path,
            "activation_link": activation_link,
        },
    )


@login_required
def resend_verification(request):
    if request.method != "POST":
        return redirect("verify_email")

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.email_verified:
        messages.info(request, "Your email is already verified.")
        return redirect("profile")

    next_path = request.POST.get("next") or request.GET.get("next", "")
    activation_link = build_activation_link(request, request.user, next_path)
    send_activation_email(request, request.user)
    messages.success(
        request,
        f"Verification email sent to {request.user.email}.",
    )
    from django.conf import settings as django_settings

    if django_settings.DEBUG:
        messages.warning(
            request,
            f"DEV: Or open this link now: {activation_link}",
        )

    next_url = request.POST.get("next") or request.GET.get("next", "")
    if next_url:
        return redirect(f"{reverse('verify_email')}?next={next_url}")
    return redirect("verify_email")


@login_required
def notifications_list(request):
    from core.models import Notification

    notifications = Notification.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "auth/notifications.html", {"notifications": notifications})
