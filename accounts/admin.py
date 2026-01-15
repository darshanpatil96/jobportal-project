from django.contrib import admin
from .models import UserProfile, Notification


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "full_name", "company_name", "email_verified")
    list_filter = ("role", "email_verified")
    search_fields = ("user__username", "full_name", "company_name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__username", "message")
