from django.contrib import admin
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "employer", "category", "job_type", "status", "posted_at")
    list_filter = ("status", "job_type", "category", "posted_at")
    search_fields = ("title", "company", "employer__user__username")
