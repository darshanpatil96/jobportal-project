"""
Shared authentication routes — used by both candidates and employers.
Login, register, email verification, password reset.
"""

from django.urls import include, path

from core import views

urlpatterns = [
    # Django built-in auth (password reset, etc.)
    path("", include("django.contrib.auth.urls")),

    # Custom auth views
    path("accounts/login/", views.login_user, name="login"),
    path("accounts/logout/", views.logout_user, name="logout"),
    path("accounts/register/", views.register_user, name="register"),
    path(
        "accounts/activate/<uidb64>/<token>/",
        views.activate_account,
        name="activate_account",
    ),
    path("accounts/verify-email/", views.verify_email, name="verify_email"),
    path(
        "accounts/resend-verification/",
        views.resend_verification,
        name="resend_verification",
    ),
    path("accounts/notifications/", views.notifications_list, name="notifications"),
]
