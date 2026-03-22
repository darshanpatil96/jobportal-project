from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/login/", views.login_user, name="login"),
    path("accounts/register/", views.register_user, name="register"),
    path("accounts/profile/", views.profile_detail, name="profile"),
    path("accounts/profile/edit/", views.profile_edit, name="profile_edit"),
    path("accounts/notifications/", views.notifications_list, name="notifications"),
    path(
        "accounts/activate/<uidb64>/<token>/",
        views.activate_account,
        name="activate_account",
    ),
    path("", include("django.contrib.auth.urls")),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/create/", views.create_job, name="create_job"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:job_id>/edit/", views.edit_job, name="edit_job"),
    path("jobs/<int:job_id>/delete/", views.delete_job, name="delete_job"),
    path("jobs/<int:job_id>/apply/", views.apply_job, name="apply_job"),
    path("jobs/<int:job_id>/save/", views.toggle_save_job, name="toggle_save_job"),
    path(
        "jobs/<int:job_id>/applications/",
        views.job_applications,
        name="job_applications",
    ),
    path("jobs/saved/", views.saved_jobs, name="saved_jobs"),
    path("jobs/applications/", views.my_applications, name="my_applications"),
    path(
        "jobs/applications/<int:app_id>/edit/",
        views.edit_application,
        name="edit_application",
    ),
    path(
        "jobs/applications/<int:app_id>/withdraw/",
        views.withdraw_application,
        name="withdraw_application",
    ),
    path("dashboard/", views.jobseeker_dashboard, name="jobseeker_dashboard"),
    path("employer/dashboard/", views.employer_dashboard, name="employer_dashboard"),
    path("companies/", views.companies, name="companies"),
    path("companies/<int:company_id>/", views.company_detail, name="company_detail"),
    path("about/", views.about, name="about"),
]
