from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserProfileForm
from .models import UserProfile, Notification
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.mail import send_mail
from .tokens import account_activation_token


def register_user(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()  # profile & role handled in form.save()

            # Send activation email
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            activation_link = request.build_absolute_uri(
                reverse("activate_account", kwargs={"uidb64": uid, "token": token})
            )

            subject = "Verify your email for JobPortal"
            message = (
                f"Hi {user.username},\n\n"
                f"Please click the link below to verify your email address:\n\n"
                f"{activation_link}\n\n"
                f"If you did not sign up, you can ignore this email."
            )
            send_mail(subject, message, None, [user.email])

            login(request, user)  # optional: keep them logged in
            messages.info(
                request,
                "Registration successful. We have sent a verification email to your address.",
            )
            return redirect("home")
    else:
        form = UserRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if not profile.email_verified:
            profile.email_verified = True
            profile.save()
            messages.success(request, "Your email has been verified.")
        return redirect("login")
    else:
        messages.error(request, "Activation link is invalid or expired.")
        return redirect("login")




def login_user(request):
    """Login view using Django's AuthenticationForm to match the template."""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if hasattr(user, "userprofile"):
                if user.userprofile.role == "employer":
                    return redirect("employer_dashboard")
                else:
                    return redirect("jobseeker_dashboard")
            return redirect("job_list")
    else:
        form = AuthenticationForm(request)

    return render(request, "accounts/login.html", {"form": form})


@login_required
def profile_detail(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, "accounts/profile.html", {"profile": profile})


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
    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
def notifications_list(request):
    """List notifications for the logged-in user and mark them as read on view."""
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")

    # Mark all as read when visiting the page
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, "accounts/notifications_list.html", {"notifications": notifications})


# signup_view removed: we now use only /accounts/register/ for registration.
