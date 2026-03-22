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

    class Meta:
        ordering = ["-posted_at"]

    def __str__(self):
        return self.title


class Application(models.Model):
    STATUS_CHOICES = [
        ("Applied", "Applied"),
        ("Under Review", "Under Review"),
        ("Shortlisted", "Shortlisted"),
        ("Interview", "Interview"),
        ("Rejected", "Rejected"),
        ("Hired", "Hired"),
        ("Withdrawn", "Withdrawn"),
    ]

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
        return f"{self.user.username} → {self.job.title}"


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
