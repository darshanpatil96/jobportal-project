from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Application
from accounts.models import Notification


@receiver(pre_save, sender=Application)
def store_old_status(sender, instance, **kwargs):
    """Store the previous status on the instance before saving.

    This lets us detect changes in post_save without an extra query there.
    """
    if not instance.pk:
        instance._old_status = None
        return

    try:
        old = Application.objects.get(pk=instance.pk)
        instance._old_status = old.status
    except Application.DoesNotExist:
        instance._old_status = None


def _notify_employer_new_application(application: Application) -> None:
    job = application.job
    employer_profile = job.employer
    employer_user = employer_profile.user

    subject = f"New application for {job.title}"
    message = (
        f"You have received a new application for your job '{job.title}'.\n\n"
        f"Candidate: {application.user.username}\n"
        f"Status: {application.status}\n\n"
        f"Please log in to your employer dashboard to review this application."
    )

    if employer_user.email:
        send_mail(
            subject,
            message,
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
            [employer_user.email],
            fail_silently=True,
        )

    # In-app notification for employer
    Notification.objects.create(
        user=employer_user,
        message=f"New application from {application.user.username} for {job.title}",
    )


def _notify_candidate_status_change(application: Application, old_status: str | None) -> None:
    candidate = application.user
    job = application.job

    subject = f"Your application status for {job.title} has changed"
    message = (
        f"Hi {candidate.username},\n\n"
        f"The status of your application for '{job.title}' has changed to: {application.status}."
    )
    if old_status:
        message += f" (previously: {old_status})"
    message += "\n\nPlease log in to your dashboard for more details."

    if candidate.email:
        send_mail(
            subject,
            message,
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
            [candidate.email],
            fail_silently=True,
        )

    # In-app notification for candidate
    Notification.objects.create(
        user=candidate,
        message=f"Your application for {job.title} is now '{application.status}'.",
    )


@receiver(post_save, sender=Application)
def application_post_save(sender, instance, created, **kwargs):
    """Send email + in-app notifications on create and status change.

    - On create: notify employer about new application.
    - On status change: notify candidate about new status.
    """
    # New application submitted
    if created:
        _notify_employer_new_application(instance)
        # Optional: candidate confirmation notification
        Notification.objects.create(
            user=instance.user,
            message=f"Your application for {instance.job.title} has been submitted.",
        )
        return

    # Existing application updated – check if status changed
    old_status = getattr(instance, "_old_status", None)
    if old_status and old_status != instance.status:
        _notify_candidate_status_change(instance, old_status)