"""
Company Workspace models — SaaS-ready employer isolation.

This module introduces the CompanyWorkspace as the central entity for
employer experiences. It separates company identity from user identity,
enabling:
  - Multiple team members per company
  - Role-based access within a workspace (owner, admin, recruiter, viewer)
  - Company branding independent of individual users
  - Future SaaS billing per workspace
  - Workspace-level settings and preferences

Migration strategy:
  - CompanyWorkspace is OPTIONAL initially
  - Existing Job.employer (UserProfile FK) continues working
  - Job.workspace (nullable FK) is added for new architecture
  - A data migration will link existing jobs to auto-created workspaces
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify


class CompanyWorkspace(models.Model):
    """
    Isolated workspace for each employer/company.

    This is the top-level entity for the employer ATS experience.
    All jobs, candidates, interviews, and analytics are scoped to a workspace.
    """

    PLAN_CHOICES = [
        ("free", "Free"),
        ("starter", "Starter"),
        ("professional", "Professional"),
        ("enterprise", "Enterprise"),
    ]

    # Identity
    name = models.CharField(max_length=200, help_text="Company display name")
    slug = models.SlugField(max_length=220, unique=True, help_text="URL-safe identifier")
    description = models.TextField(blank=True)
    website = models.URLField(blank=True, default="")
    logo = models.ImageField(upload_to="workspace_logos/", blank=True, null=True)

    # Branding
    primary_color = models.CharField(
        max_length=7, default="#6366f1", help_text="Hex color for workspace branding"
    )
    tagline = models.CharField(max_length=200, blank=True)

    # Location & Industry
    headquarters = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True, help_text="e.g. 50-200")

    # Ownership
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="owned_workspaces",
        help_text="Primary account owner (billing contact)",
    )

    # SaaS fields (future billing)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")
    max_jobs = models.IntegerField(default=10, help_text="Max active job postings")
    max_members = models.IntegerField(default=3, help_text="Max team members")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Company Workspace"
        verbose_name_plural = "Company Workspaces"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            base_slug = self.slug
            counter = 1
            while CompanyWorkspace.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def active_jobs_count(self):
        return self.jobs.filter(status="Open").count()

    @property
    def total_applications_count(self):
        from core.models import Application
        return Application.objects.filter(job__workspace=self).exclude(
            status="Withdrawn"
        ).count()


class WorkspaceMember(models.Model):
    """
    Team membership within a workspace.

    Enables multi-user access to the same company's ATS.
    Each member has a role that determines their permissions.
    """

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("recruiter", "Recruiter"),
        ("hiring_manager", "Hiring Manager"),
        ("viewer", "Viewer"),
    ]

    workspace = models.ForeignKey(
        CompanyWorkspace,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="recruiter")
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workspace_invitations_sent",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("workspace", "user")
        ordering = ["role", "joined_at"]
        verbose_name = "Workspace Member"
        verbose_name_plural = "Workspace Members"

    def __str__(self):
        return f"{self.user.username} @ {self.workspace.name} ({self.role})"

    @property
    def can_manage_jobs(self):
        return self.role in ("owner", "admin", "recruiter")

    @property
    def can_manage_candidates(self):
        return self.role in ("owner", "admin", "recruiter", "hiring_manager")

    @property
    def can_schedule_interviews(self):
        return self.role in ("owner", "admin", "recruiter", "hiring_manager")

    @property
    def can_manage_team(self):
        return self.role in ("owner", "admin")

    @property
    def can_view_analytics(self):
        return self.role in ("owner", "admin", "recruiter")

    @property
    def can_delete_workspace(self):
        return self.role == "owner"


class WorkspaceInvitation(models.Model):
    """
    Pending invitation to join a workspace.

    Supports invite-by-email for users who haven't registered yet.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("expired", "Expired"),
    ]

    workspace = models.ForeignKey(
        CompanyWorkspace,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField(help_text="Invitee email address")
    role = models.CharField(
        max_length=20,
        choices=WorkspaceMember.ROLE_CHOICES,
        default="recruiter",
    )
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invite {self.email} → {self.workspace.name} ({self.status})"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
