"""
Public routes — no authentication required.
Home page, about, company directory.
"""

from django.urls import path

from core import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("companies/", views.companies, name="companies"),
    path("companies/<int:company_id>/", views.company_detail, name="company_detail"),
]
