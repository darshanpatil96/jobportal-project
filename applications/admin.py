from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "status", "applied_at")
    list_filter = ("status", "job__category", "job__job_type", "applied_at")
    search_fields = ("user__username", "job__title", "job__company")
