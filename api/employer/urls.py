from django.urls import path

from . import views

urlpatterns = [
    # Dashboard
    path("dashboard/", views.EmployerDashboardView.as_view(), name="api_employer_dashboard"),

    # Jobs
    path("jobs/", views.EmployerJobListView.as_view(), name="api_employer_jobs"),
    path("jobs/create/", views.EmployerJobCreateView.as_view(), name="api_employer_job_create"),
    path("jobs/<int:pk>/", views.EmployerJobDetailView.as_view(), name="api_employer_job_detail"),
    path("jobs/<int:pk>/update/", views.EmployerJobUpdateView.as_view(), name="api_employer_job_update"),

    # Candidates / Applications
    path("candidates/", views.EmployerCandidateListView.as_view(), name="api_employer_candidates"),
    path("candidates/<int:pk>/", views.EmployerCandidateDetailView.as_view(), name="api_employer_candidate_detail"),
    path("candidates/<int:pk>/status/", views.UpdateCandidateStatusView.as_view(), name="api_employer_update_status"),

    # Interviews
    path("interviews/", views.EmployerInterviewListView.as_view(), name="api_employer_interviews"),
    path("interviews/schedule/", views.ScheduleInterviewView.as_view(), name="api_employer_schedule_interview"),
    path("interviews/<int:pk>/status/", views.UpdateInterviewStatusView.as_view(), name="api_employer_update_interview"),

    # Analytics
    path("analytics/", views.EmployerAnalyticsView.as_view(), name="api_employer_analytics"),
]
