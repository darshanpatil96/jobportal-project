from django.db import transaction

from core.models import ApplicationTimelineEvent


class TimelineService:
    """Audit-style application activity log."""

    @staticmethod
    def log(application, event_type: str, message: str, metadata: dict | None = None):
        return ApplicationTimelineEvent.objects.create(
            application=application,
            event_type=event_type,
            message=message[:500],
            metadata=metadata or {},
        )

    @staticmethod
    def log_applied(application):
        return TimelineService.log(
            application,
            "applied",
            f"{application.user.username} applied to {application.job.title}.",
            {"status": application.status},
        )

    @staticmethod
    def log_resume_parsed(application, parse_status: str, skill_count: int = 0):
        return TimelineService.log(
            application,
            "resume_parsed",
            f"Resume parsed ({parse_status}). {skill_count} skills detected.",
            {"parse_status": parse_status, "skill_count": skill_count},
        )

    @staticmethod
    def log_match_computed(application, overall_score: float):
        return TimelineService.log(
            application,
            "match_computed",
            f"AI match score generated: {overall_score:.0f}% compatibility.",
            {"overall_score": overall_score},
        )

    @staticmethod
    def log_status_changed(application, old_status: str, new_status: str, updated_by=None):
        by = updated_by.username if updated_by else "system"
        return TimelineService.log(
            application,
            "status_changed",
            f"Status changed from {old_status} to {new_status} by {by}.",
            {"old_status": old_status, "new_status": new_status},
        )

    @staticmethod
    def log_interview_scheduled(application, interview):
        return TimelineService.log(
            application,
            "interview_scheduled",
            f"{interview.interview_type} interview scheduled for "
            f"{interview.scheduled_time.strftime('%b %d, %Y %H:%M')}.",
            {
                "interview_id": interview.id,
                "interview_type": interview.interview_type,
                "scheduled_time": interview.scheduled_time.isoformat(),
            },
        )

    @staticmethod
    def log_interview_completed(application, interview):
        return TimelineService.log(
            application,
            "interview_completed",
            f"{interview.interview_type} interview marked completed.",
            {"interview_id": interview.id},
        )

    @staticmethod
    def get_timeline(application):
        return application.timeline_events.all()
