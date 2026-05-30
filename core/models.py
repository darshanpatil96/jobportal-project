from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("jobseeker", "Job Seeker"),
        ("employer", "Employer"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default="jobseeker")
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    resume = models.FileField(upload_to="profiles/", blank=True, null=True)
    company_name = models.CharField(max_length=200, blank=True, default="")
    company_website = models.URLField(blank=True, default="")
    company_logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    company_description = models.TextField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return self.user.username


class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"


class Job(models.Model):
    STATUS_CHOICES = [
        ("Open", "Open"),
        ("Closed", "Closed"),
        ("Draft", "Draft"),
    ]
    JOB_TYPE_CHOICES = [
        ("Full-Time", "Full-Time"),
        ("Part-Time", "Part-Time"),
        ("Internship", "Internship"),
        ("Remote", "Remote"),
    ]

    employer = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    workspace = models.ForeignKey(
        "core.CompanyWorkspace",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobs",
        help_text="Company workspace (auto-linked for new jobs).",
    )
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    salary = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=100)
    job_type = models.CharField(
        max_length=100, choices=JOB_TYPE_CHOICES, default="Full-Time"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Open")
    posted_at = models.DateTimeField(auto_now_add=True)
    required_skills = models.JSONField(
        default=list,
        blank=True,
        help_text="Optional explicit skills for matching; auto-extracted from description if empty.",
    )

    class Meta:
        ordering = ["-posted_at"]

    def __str__(self):
        return self.title


class Application(models.Model):
    STATUS_CHOICES = [
        ("Applied", "Applied"),
        ("Screening", "Screening"),
        ("Technical Round", "Technical Round"),
        ("HR Round", "HR Round"),
        ("Final Review", "Final Review"),
        ("Offer Sent", "Offer Sent"),
        ("Hired", "Hired"),
        ("Rejected", "Rejected"),
        ("Withdrawn", "Withdrawn"),
    ]

    # Maps legacy DB values to the new pipeline (migration + runtime normalization).
    LEGACY_STATUS_MAP = {
        "Under Review": "Screening",
        "Shortlisted": "Screening",
        "Interview": "Technical Round",
    }

    TERMINAL_STATUSES = frozenset({"Hired", "Rejected", "Withdrawn"})

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    cover_letter = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to="applications/", blank=True, null=True)
    qualification = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    experience = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Applied")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "job"],
                name="unique_application_per_user_job",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.job.title}"

    @classmethod
    def normalize_status(cls, status):
        return cls.LEGACY_STATUS_MAP.get(status, status)

    @property
    def normalized_status(self):
        return self.normalize_status(self.status)


class ParsedResume(models.Model):
    PARSE_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="parsed_resumes"
    )
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="parsed_resume",
        null=True,
        blank=True,
    )
    source_file = models.CharField(max_length=500, blank=True)
    raw_text = models.TextField(blank=True)
    parsed_data = models.JSONField(default=dict, blank=True)
    parse_status = models.CharField(
        max_length=20, choices=PARSE_STATUS_CHOICES, default="pending"
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"ParsedResume({self.user.username}, {self.parse_status})"


class ApplicationMatchScore(models.Model):
    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="match_score"
    )
    overall_score = models.FloatField(default=0.0)
    category_scores = models.JSONField(default=dict, blank=True)
    skill_details = models.JSONField(default=dict, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    embedding_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Reserved for future vector/embedding storage.",
    )
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-overall_score"]

    def __str__(self):
        return f"Match {self.overall_score:.0f}% — {self.application}"


class Interview(models.Model):
    INTERVIEW_TYPE_CHOICES = [
        ("Online", "Online"),
        ("Offline", "Offline"),
        ("Technical", "Technical"),
        ("HR", "HR"),
        ("Screening", "Screening"),
    ]
    STATUS_CHOICES = [
        ("Scheduled", "Scheduled"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
        ("Rescheduled", "Rescheduled"),
    ]

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="interviews"
    )
    scheduled_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="scheduled_interviews"
    )
    scheduled_time = models.DateTimeField()
    meeting_link = models.URLField(blank=True, default="")
    interview_type = models.CharField(
        max_length=20, choices=INTERVIEW_TYPE_CHOICES, default="Online"
    )
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Scheduled"
    )
    reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set by future reminder cron/Celery task.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_time"]

    def __str__(self):
        return f"{self.interview_type} — {self.application} @ {self.scheduled_time}"


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="status_history"
    )
    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name_plural = "Application status histories"

    def __str__(self):
        return f"{self.old_status} -> {self.new_status}"


class ApplicationTimelineEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ("applied", "Applied"),
        ("resume_parsed", "Resume Parsed"),
        ("match_computed", "Match Score Generated"),
        ("reviewed", "Reviewed"),
        ("status_changed", "Status Changed"),
        ("interview_scheduled", "Interview Scheduled"),
        ("interview_completed", "Interview Completed"),
        ("interview_cancelled", "Interview Cancelled"),
        ("offer_sent", "Offer Sent"),
        ("hired", "Hired"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
    ]

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="timeline_events"
    )
    event_type = models.CharField(max_length=40, choices=EVENT_TYPE_CHOICES)
    message = models.CharField(max_length=500)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_type}: {self.message[:40]}"


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    pass


account_activation_token = AccountActivationTokenGenerator()


# ── Workspace models (SaaS architecture) ─────────────────────────────────────
from core.models_workspace import (  # noqa: F401, E402
    CompanyWorkspace,
    WorkspaceMember,
    WorkspaceInvitation,
)
