from django.db import models
from accounts.models import UserProfile
from django.contrib.auth.models import User

class Job(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('Draft', 'Draft'),
    ]

    employer = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    salary = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=100)

    job_type = models.CharField(
        max_length=100,
        choices=[
            ('Full-Time', 'Full-Time'),
            ('Part-Time', 'Part-Time'),
            ('Internship', 'Internship'),
            ('Remote', 'Remote'),
        ],
        default='Full-Time',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Open'
    )

    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class SavedJob(models.Model):
    """
    A job bookmarked by a job seeker.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"