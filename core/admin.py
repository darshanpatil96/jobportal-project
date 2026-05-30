from django.contrib import admin
from .models import (
    UserProfile,
    Notification,
    Job,
    Application,
    SavedJob,
    ParsedResume,
    ApplicationMatchScore,
    Interview,
    ApplicationStatusHistory,
    ApplicationTimelineEvent,
    CompanyWorkspace,
    WorkspaceMember,
    WorkspaceInvitation,
)


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


@admin.register(ParsedResume)
class ParsedResumeAdmin(admin.ModelAdmin):
    list_display = ["user", "application", "parse_status", "updated_at"]
    list_filter = ["parse_status"]
    search_fields = ["user__username"]


@admin.register(ApplicationMatchScore)
class ApplicationMatchScoreAdmin(admin.ModelAdmin):
    list_display = ["application", "overall_score", "computed_at"]
    ordering = ["-overall_score"]


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = [
        "application",
        "interview_type",
        "scheduled_time",
        "status",
        "scheduled_by",
    ]
    list_filter = ["status", "interview_type"]
    date_hierarchy = "scheduled_time"


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["application", "old_status", "new_status", "updated_by", "updated_at"]
    list_filter = ["new_status"]


@admin.register(ApplicationTimelineEvent)
class ApplicationTimelineEventAdmin(admin.ModelAdmin):
    list_display = ["application", "event_type", "message", "created_at"]
    list_filter = ["event_type"]
    date_hierarchy = "created_at"


# ── Workspace Admin ──────────────────────────────────────────────────────────


class WorkspaceMemberInline(admin.TabularInline):
    model = WorkspaceMember
    extra = 0
    fields = ["user", "role", "is_active", "joined_at"]
    readonly_fields = ["joined_at"]


@admin.register(CompanyWorkspace)
class CompanyWorkspaceAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "plan", "is_active", "created_at"]
    list_filter = ["plan", "is_active", "industry"]
    search_fields = ["name", "owner__username"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [WorkspaceMemberInline]


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ["user", "workspace", "role", "is_active", "joined_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["user__username", "workspace__name"]


@admin.register(WorkspaceInvitation)
class WorkspaceInvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "workspace", "role", "status", "created_at"]
    list_filter = ["status", "role"]
    search_fields = ["email", "workspace__name"]
