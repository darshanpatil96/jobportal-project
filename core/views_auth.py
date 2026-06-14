"""
Shared authentication views — used by both candidates and employers.

Email verification has been removed. Users can register, login,
and apply for jobs immediately without any verification step.
"""

from django.contrib import messages
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from core.forms import UserRegisterForm
from core.models import UserProfile


def register_user(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to ARTISAN.")
            if hasattr(user, "userprofile") and user.userprofile.role == "employer":
                return redirect("employer_dashboard")
            return redirect("jobseeker_dashboard")
    else:
        form = UserRegisterForm()
    return render(request, "auth/register.html", {"form": form})


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
def notifications_list(request):
    from core.models import Notification

    notifications = Notification.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "auth/notifications.html", {"notifications": notifications})
