from django.urls import path, include
from . import views

urlpatterns = [
    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register"),
    path("profile/", views.profile_detail, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("notifications/", views.notifications_list, name="notifications"),

    path("activate/<uidb64>/<token>/", views.activate_account, name="activate_account"),

    # Built-in Django auth URLs (password reset, etc.)
    # Login view here is overridden by our custom login_user above.
    path("", include("django.contrib.auth.urls")),
]
