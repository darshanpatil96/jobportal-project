from django.urls import path

from . import views

urlpatterns = [
    # Jobs
    path("jobs/", views.JobListView.as_view(), name="api_job_list"),
    path("jobs/<int:pk>/", views.JobDetailView.as_view(), name="api_job_detail"),

    # Applications
    path("applications/", views.ApplicationListView.as_view(), name="api_my_applications"),
    path("applications/apply/", views.ApplyJobView.as_view(), name="api_apply_job"),
    path("applications/<int:pk>/", views.ApplicationDetailView.as_view(), name="api_application_detail"),
    path("applications/<int:pk>/withdraw/", views.WithdrawApplicationView.as_view(), name="api_withdraw_application"),
    path("applications/<int:pk>/timeline/", views.ApplicationTimelineView.as_view(), name="api_application_timeline"),

    # Saved Jobs
    path("saved-jobs/", views.SavedJobListView.as_view(), name="api_saved_jobs"),
    path("saved-jobs/toggle/", views.ToggleSaveJobView.as_view(), name="api_toggle_save_job"),

    # Dashboard
    path("dashboard/", views.CandidateDashboardView.as_view(), name="api_candidate_dashboard"),
]
