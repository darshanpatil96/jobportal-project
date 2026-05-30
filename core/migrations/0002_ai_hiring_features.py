# Generated manually for AI hiring features

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrate_legacy_application_statuses(apps, schema_editor):
    Application = apps.get_model("core", "Application")
    mapping = {
        "Under Review": "Screening",
        "Shortlisted": "Screening",
        "Interview": "Technical Round",
    }
    for old, new in mapping.items():
        Application.objects.filter(status=old).update(status=new)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="required_skills",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Optional explicit skills for matching; auto-extracted from description if empty.",
            ),
        ),
        migrations.AlterField(
            model_name="application",
            name="status",
            field=models.CharField(
                choices=[
                    ("Applied", "Applied"),
                    ("Screening", "Screening"),
                    ("Technical Round", "Technical Round"),
                    ("HR Round", "HR Round"),
                    ("Final Review", "Final Review"),
                    ("Offer Sent", "Offer Sent"),
                    ("Hired", "Hired"),
                    ("Rejected", "Rejected"),
                    ("Withdrawn", "Withdrawn"),
                ],
                default="Applied",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="ParsedResume",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("source_file", models.CharField(blank=True, max_length=500)),
                ("raw_text", models.TextField(blank=True)),
                ("parsed_data", models.JSONField(blank=True, default=dict)),
                (
                    "parse_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("skipped", "Skipped"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "application",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parsed_resume",
                        to="core.application",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parsed_resumes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="ApplicationMatchScore",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("overall_score", models.FloatField(default=0.0)),
                ("category_scores", models.JSONField(blank=True, default=dict)),
                ("skill_details", models.JSONField(blank=True, default=dict)),
                ("missing_skills", models.JSONField(blank=True, default=list)),
                (
                    "embedding_snapshot",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Reserved for future vector/embedding storage.",
                    ),
                ),
                ("computed_at", models.DateTimeField(auto_now=True)),
                (
                    "application",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="match_score",
                        to="core.application",
                    ),
                ),
            ],
            options={"ordering": ["-overall_score"]},
        ),
        migrations.CreateModel(
            name="Interview",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("scheduled_time", models.DateTimeField()),
                ("meeting_link", models.URLField(blank=True, default="")),
                (
                    "interview_type",
                    models.CharField(
                        choices=[
                            ("Online", "Online"),
                            ("Offline", "Offline"),
                            ("Technical", "Technical"),
                            ("HR", "HR"),
                            ("Screening", "Screening"),
                        ],
                        default="Online",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Scheduled", "Scheduled"),
                            ("Completed", "Completed"),
                            ("Cancelled", "Cancelled"),
                            ("Rescheduled", "Rescheduled"),
                        ],
                        default="Scheduled",
                        max_length=20,
                    ),
                ),
                (
                    "reminder_sent_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Set by future reminder cron/Celery task.",
                        null=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interviews",
                        to="core.application",
                    ),
                ),
                (
                    "scheduled_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scheduled_interviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["scheduled_time"]},
        ),
        migrations.CreateModel(
            name="ApplicationStatusHistory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("old_status", models.CharField(max_length=30)),
                ("new_status", models.CharField(max_length=30)),
                ("notes", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now_add=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="core.application",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Application status histories",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="ApplicationTimelineEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        choices=[
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
                        ],
                        max_length=40,
                    ),
                ),
                ("message", models.CharField(max_length=500)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="timeline_events",
                        to="core.application",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.RunPython(
            migrate_legacy_application_statuses,
            migrations.RunPython.noop,
        ),
    ]
