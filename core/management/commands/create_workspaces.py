"""
Management command to create workspaces for existing employers.

Run once after deploying the workspace feature:
    python manage.py create_workspaces

This will:
1. Create a CompanyWorkspace for each employer with a company_name
2. Add the employer as the workspace owner
3. Link all their existing jobs to the new workspace
"""

from django.core.management.base import BaseCommand

from core.models import Job, UserProfile
from core.services.employer.workspace import WorkspaceService


class Command(BaseCommand):
    help = "Create workspaces for existing employers and link their jobs."

    def handle(self, *args, **options):
        employers = UserProfile.objects.filter(role="employer").exclude(company_name="")
        created = 0
        linked_jobs = 0

        for profile in employers:
            workspace = WorkspaceService.auto_create_from_profile(profile)
            if workspace:
                # Link existing jobs to workspace
                jobs_updated = Job.objects.filter(
                    employer=profile, workspace__isnull=True
                ).update(workspace=workspace)
                linked_jobs += jobs_updated
                created += 1
                self.stdout.write(
                    f"  ✓ {profile.company_name}: workspace created, "
                    f"{jobs_updated} jobs linked"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone: {created} workspaces created, {linked_jobs} jobs linked."
            )
        )
