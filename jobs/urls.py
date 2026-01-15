from django.urls import path
from . import views

urlpatterns = [
    # Jobseeker dashboard
    path('dashboard/', views.jobseeker_dashboard, name='jobseeker_dashboard'),
    
    # Job list: http://127.0.0.1:8000/jobs/
    path('', views.job_list, name='job_list'),

    # Static pages
    path('companies/', views.companies, name='companies'),
    path("companies/<int:company_id>/", views.company_detail, name="company_detail"),
    path('about/', views.about, name='about'),

    # Employer dashboard: http://127.0.0.1:8000/jobs/employer/dashboard/
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),

    # Create job: http://127.0.0.1:8000/jobs/create/
    path('create/', views.create_job, name='create_job'),
    path("<int:job_id>/edit/", views.edit_job, name="edit_job"),      # NEW
    path("<int:job_id>/delete/", views.delete_job, name="delete_job"),# NEW

    # Job detail: http://127.0.0.1:8000/jobs/1/
    path('<int:job_id>/', views.job_detail, name='job_detail'),

    path("<int:job_id>/apply/", views.apply_job, name="apply_job"),

    # My Applications
    path("applications/", views.my_applications, name="my_applications"),
    path("applications/<int:app_id>/edit/", views.edit_application, name="edit_application"),
    path("applications/<int:app_id>/withdraw/", views.withdraw_application, name="withdraw_application"),

    # NEW: applications for a specific job (employer-only)
    path("<int:job_id>/applications/", views.job_applications, name="job_applications"),

    # Saved jobs
    path("saved/", views.saved_jobs, name="saved_jobs"),
    path("<int:job_id>/save/", views.toggle_save_job, name="toggle_save_job"),
]
