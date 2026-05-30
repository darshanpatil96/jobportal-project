from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.models import Interview
from core.hiring.timeline import TimelineService
from core.hiring.notifications import NotificationService


class InterviewService:
    """Interview scheduling with notification and reminder-ready fields."""

    @classmethod
    @transaction.atomic
    def schedule(
        cls,
        application,
        scheduled_by,
        scheduled_time,
        interview_type: str = "Online",
        meeting_link: str = "",
        notes: str = "",
    ) -> Interview:
        if scheduled_time <= timezone.now():
            raise ValidationError("Interview must be scheduled in the future.")

        interview = Interview.objects.create(
            application=application,
            scheduled_by=scheduled_by,
            scheduled_time=scheduled_time,
            interview_type=interview_type,
            meeting_link=meeting_link or "",
            notes=notes,
            status="Scheduled",
        )

        TimelineService.log_interview_scheduled(application, interview)

        candidate = application.user
        msg = (
            f"Interview scheduled for '{application.job.title}' on "
            f"{scheduled_time.strftime('%b %d, %Y at %H:%M')} ({interview_type})."
        )
        NotificationService.notify(candidate, msg)

        cls._send_interview_email(candidate, application, interview)

        return interview

    @classmethod
    @transaction.atomic
    def update_status(cls, interview: Interview, new_status: str) -> Interview:
        if new_status not in dict(Interview.STATUS_CHOICES):
            raise ValidationError(f"Invalid interview status: {new_status}")

        interview.status = new_status
        interview.save(update_fields=["status", "updated_at"])

        application = interview.application
        if new_status == "Completed":
            TimelineService.log_interview_completed(application, interview)
            NotificationService.notify(
                application.user,
                f"Your {interview.interview_type} interview for "
                f"'{application.job.title}' was marked completed.",
            )
        elif new_status == "Cancelled":
            TimelineService.log(
                application,
                "interview_cancelled",
                f"{interview.interview_type} interview cancelled.",
                {"interview_id": interview.id},
            )
            NotificationService.notify(
                application.user,
                f"Interview for '{application.job.title}' was cancelled.",
            )

        return interview

    @classmethod
    def get_pending_reminders(cls, hours_before: int = 24):
        """Query interviews needing reminders (for future Celery/cron)."""
        from datetime import timedelta

        window_start = timezone.now()
        window_end = window_start + timedelta(hours=hours_before)
        return Interview.objects.filter(
            status="Scheduled",
            scheduled_time__gte=window_start,
            scheduled_time__lte=window_end,
            reminder_sent_at__isnull=True,
        ).select_related("application__user", "application__job")

    @staticmethod
    def _send_interview_email(candidate, application, interview):
        subject = f"Interview invitation — {application.job.title}"
        body = (
            f"Hi {candidate.username},\n\n"
            f"You have been invited to a {interview.interview_type} interview "
            f"for {application.job.title}.\n\n"
            f"Date/Time: {interview.scheduled_time}\n"
        )
        if interview.meeting_link:
            body += f"Meeting link: {interview.meeting_link}\n"
        if interview.notes:
            body += f"\nNotes:\n{interview.notes}\n"
        body += "\nGood luck!\n"
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [candidate.email],
                fail_silently=True,
            )
        except Exception:
            pass
