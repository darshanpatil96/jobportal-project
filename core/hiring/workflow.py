"""
Orchestrates post-application AI processing:
resume parse → match score → timeline → notifications.
"""

from __future__ import annotations

import logging

from django.db import transaction

from core.models import Application, ApplicationMatchScore, ParsedResume
from core.ai import ResumeParserService, MatchingEngineService
from core.hiring.timeline import TimelineService
from core.hiring.notifications import NotificationService

logger = logging.getLogger(__name__)

_parser = ResumeParserService()
_matcher = MatchingEngineService()


class ApplicationWorkflowService:
    @classmethod
    @transaction.atomic
    def process_new_application(cls, application: Application):
        """Run after Application is created or resume is updated."""
        TimelineService.log_applied(application)

        parsed_record = cls._parse_resume(application)
        cls._compute_match(application, parsed_record)

        employer_user = application.job.employer.user
        NotificationService.notify(
            employer_user,
            f"New application from {application.user.username} for "
            f"'{application.job.title}'.",
        )
        NotificationService.notify(
            application.user,
            f"Your application for '{application.job.title}' was submitted.",
        )

    @classmethod
    def _parse_resume(cls, application: Application) -> ParsedResume | None:
        resume_file = application.resume
        if not resume_file:
            profile = getattr(application.user, "userprofile", None)
            resume_file = profile.resume if profile else None

        parsed_record, _ = ParsedResume.objects.get_or_create(
            application=application,
            defaults={"user": application.user},
        )

        if not resume_file:
            parsed_record.parse_status = "skipped"
            parsed_record.error_message = "No resume uploaded"
            parsed_record.save(
                update_fields=["parse_status", "error_message", "updated_at"]
            )
            TimelineService.log_resume_parsed(application, "skipped", 0)
            return parsed_record

        result = _parser.parse_file(resume_file)
        parsed_record.raw_text = result.get("raw_text", "")
        parsed_record.parsed_data = {
            k: result.get(k)
            for k in (
                "skills",
                "education",
                "experience",
                "projects",
                "certifications",
                "email",
                "phone",
                "linkedin",
                "github",
            )
        }
        parsed_record.parse_status = result.get("parse_status", "failed")
        parsed_record.error_message = result.get("error", "")
        parsed_record.source_file = result.get("source_file", resume_file.name)
        parsed_record.save()

        skill_count = len(parsed_record.parsed_data.get("skills", []))
        TimelineService.log_resume_parsed(
            application, parsed_record.parse_status, skill_count
        )

        if parsed_record.parsed_data.get("email") and not application.user.email:
            pass  # preserve user email; optional enrichment only

        return parsed_record

    @classmethod
    def _compute_match(cls, application: Application, parsed_record: ParsedResume | None):
        parsed_data = {}
        if parsed_record and parsed_record.parsed_data:
            parsed_data = {
                **parsed_record.parsed_data,
                "raw_text": parsed_record.raw_text,
            }

        job = application.job
        match_result = _matcher.compute_match(
            job.description,
            job.category,
            parsed_data,
            explicit_required_skills=job.required_skills or [],
        )

        score_obj, _ = ApplicationMatchScore.objects.update_or_create(
            application=application,
            defaults={
                "overall_score": match_result["overall_score"],
                "category_scores": match_result["category_scores"],
                "skill_details": match_result["skill_details"],
                "missing_skills": match_result["missing_skills"],
                "embedding_snapshot": match_result["embedding_snapshot"],
            },
        )

        TimelineService.log_match_computed(application, score_obj.overall_score)
        return score_obj

    @classmethod
    def reprocess_application(cls, application: Application):
        """Re-run parse + match (e.g. after resume edit)."""
        cls._parse_resume(application)
        parsed = getattr(application, "parsed_resume", None)
        cls._compute_match(application, parsed)
