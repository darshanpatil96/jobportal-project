from django.contrib import admin
from .models import UserProfile, Notification, Job, Application, SavedJob


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "full_name", "company_name", "email_verified"]
    list_filter = ["role", "email_verified"]
    search_fields = ["user__username", "full_name", "company_name"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "message", "is_read", "created_at"]
    list_filter = ["is_read"]
    search_fields = ["user__username", "message"]


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "location", "job_type", "status", "posted_at"]
    list_filter = ["status", "job_type", "category"]
    search_fields = ["title", "company", "location"]
    date_hierarchy = "posted_at"


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "status", "applied_at"]
    list_filter = ["status"]
    search_fields = ["user__username", "job__title"]
    date_hierarchy = "applied_at"


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "created_at"]
    search_fields = ["user__username", "job__title"]
