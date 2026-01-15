from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('jobseeker', 'Job Seeker'),
        ('employer', 'Employer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default="jobseeker")
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    resume = models.FileField(upload_to="profiles/", blank=True, null=True)

    # NEW employer-specific fields
    company_name = models.CharField(max_length=200, blank=True, default="")
    company_website = models.URLField(blank=True, default="")
    company_logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    company_description = models.TextField(blank=True, null=True)

    # Email verification
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Notification(models.Model):
    """Simple in-app notification for a user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"
