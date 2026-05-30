from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import Application, ApplicationStatusHistory
from core.hiring.timeline import TimelineService
from core.hiring.notifications import NotificationService


# Valid hiring pipeline transitions
VALID_TRANSITIONS = {
    "Applied": {"Screening", "Rejected", "Withdrawn"},
    "Screening": {"Technical Round", "HR Round", "Rejected", "Withdrawn"},
    "Technical Round": {"HR Round", "Final Review", "Rejected", "Withdrawn"},
    "HR Round": {"Final Review", "Offer Sent", "Rejected", "Withdrawn"},
    "Final Review": {"Offer Sent", "Hired", "Rejected", "Withdrawn"},
    "Offer Sent": {"Hired", "Rejected", "Withdrawn"},
    "Hired": set(),
    "Rejected": set(),
    "Withdrawn": set(),
}


class PipelineService:
    """Multi-step hiring pipeline with history and validation."""

    @classmethod
    def can_transition(cls, old_status: str, new_status: str) -> bool:
        old_status = Application.normalize_status(old_status)
        new_status = Application.normalize_status(new_status)
        if old_status == new_status:
            return True
        allowed = VALID_TRANSITIONS.get(old_status, set())
        return new_status in allowed

    @classmethod
    @transaction.atomic
    def transition(
        cls,
        application: Application,
        new_status: str,
        updated_by=None,
        notes: str = "",
        *,
        skip_validation: bool = False,
    ) -> Application:
        new_status = Application.normalize_status(new_status)
        old_status = Application.normalize_status(application.status)

        if not skip_validation and not cls.can_transition(old_status, new_status):
            raise ValidationError(
                f"Invalid transition from '{old_status}' to '{new_status}'."
            )

        if old_status == new_status:
            return application

        application.status = new_status
        application.save(update_fields=["status"])

        ApplicationStatusHistory.objects.create(
            application=application,
            old_status=old_status,
            new_status=new_status,
            updated_by=updated_by,
            notes=notes,
        )

        TimelineService.log_status_changed(
            application, old_status, new_status, updated_by
        )

        cls._notify_status_change(application, new_status)
        cls._log_terminal_events(application, new_status)

        return application

    @classmethod
    def _notify_status_change(cls, application, new_status: str):
        candidate = application.user
        employer_user = application.job.employer.user
        msg_candidate = (
            f"Your application for '{application.job.title}' "
            f"is now: {new_status}."
        )
        msg_employer = (
            f"Application from {candidate.username} for "
            f"'{application.job.title}' moved to {new_status}."
        )
        NotificationService.notify(candidate, msg_candidate)
        if new_status not in ("Applied",):
            NotificationService.notify(employer_user, msg_employer)

    @classmethod
    def _log_terminal_events(cls, application, new_status: str):
        if new_status == "Offer Sent":
            TimelineService.log(
                application,
                "offer_sent",
                f"Offer sent for {application.job.title}.",
            )
        elif new_status == "Hired":
            TimelineService.log(
                application,
                "hired",
                f"Candidate hired for {application.job.title}.",
            )
        elif new_status == "Rejected":
            TimelineService.log(
                application,
                "rejected",
                f"Application rejected for {application.job.title}.",
            )
        elif new_status == "Withdrawn":
            TimelineService.log(
                application,
                "withdrawn",
                f"Application withdrawn for {application.job.title}.",
            )

    @classmethod
    def get_allowed_next_statuses(cls, current_status: str) -> list[str]:
        current = Application.normalize_status(current_status)
        return sorted(VALID_TRANSITIONS.get(current, set()))
