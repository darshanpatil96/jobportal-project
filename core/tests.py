from pathlib import Path
import os
from importlib import reload

from django.conf import settings
from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import UserProfile, Job, Application


class RequirementsAndRenderTests(SimpleTestCase):
    """Tests for deployment-related behaviour (requirements + Render).

    These tests are meant to guard against accidentally re‑enabling
    Windows‑only packages in ``requirements.txt`` and to ensure that the
    Django application can be initialised in a Render‑like environment
    where those packages are not installed.
    """

    def _parse_requirements(self):
        """Return normalized, non-comment requirement lines.

        This mimics how tools like ``pip`` treat ``requirements.txt``:
        - ignores empty lines
        - ignores lines starting with ``#`` (comments)
        - strips inline comments that follow a ``#``
        """

        req_path = Path(settings.BASE_DIR) / "requirements.txt"
        requirements = []

        with req_path.open(encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    # Skip empty lines and full-line comments
                    continue

                # Remove any inline comment portion (after a '#')
                if "#" in line:
                    line = line.split("#", 1)[0].strip()

                if line:
                    requirements.append(line)

        return requirements

    def test_requirements_ignore_commented_windows_only_packages(self):
        """Windows-only packages commented out should not appear as requirements."""
        requirements = self._parse_requirements()

        # These are intentionally commented out in requirements.txt
        self.assertNotIn("pypiwin32==223", requirements)
        self.assertNotIn("pywin32==311", requirements)

        # Sanity check: a known, required package should still be present
        self.assertIn("Django==5.2.8", requirements)

    def test_wsgi_application_loads_in_render_like_environment(self):
        """Application should initialise without Windows-only packages on Render.

        We simulate a Render environment by setting a typical environment
        variable and then importing the WSGI application. If any Windows-
        only dependency were required at import time, this would raise.
        """

        # Simulate a Render deployment environment flag
        os.environ.setdefault("RENDER", "true")

        # Import and reload the WSGI module to force Django initialisation
        import jobportal.wsgi  # noqa: WPS433 (import inside function is intentional)

        reload(jobportal.wsgi)

        # Accessing the application attribute ensures initialisation completed
        self.assertIsNotNone(jobportal.wsgi.application)


class AuthViewsTestCase(TestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "securepassword123"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.profile = UserProfile.objects.create(user=self.user, role="jobseeker")

    def test_login_user(self):
        # GET login page
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/login.html")

        # POST valid login credentials
        response = self.client.post(reverse("login"), {
            "username": self.username,
            "password": self.password,
        })
        # login redirects to jobseeker_dashboard for role=jobseeker
        self.assertRedirects(response, reverse("jobseeker_dashboard"))

        # Verify user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_profile_retrieval(self):
        # Try to access profile without logging in (should redirect to login)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)
        
        # Log in first
        self.client.login(username=self.username, password=self.password)
        
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/profile.html")
        self.assertContains(response, self.username)

    def test_custom_logout(self):
        # Log in first
        self.client.login(username=self.username, password=self.password)
        
        # Verify user is authenticated
        session = self.client.session
        self.assertIn("_auth_user_id", session)

        # GET logout
        response = self.client.get(reverse("logout"))
        
        # Logout redirects to home
        self.assertRedirects(response, reverse("home"))
        
        # Verify user is logged out (no _auth_user_id in session)
        session = self.client.session
        self.assertNotIn("_auth_user_id", session)
        
        # Verify success message is in response messages
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "You have been logged out successfully.")


class PipelineServiceTests(TestCase):
    def setUp(self):
        self.employer_user = User.objects.create_user(
            username="employer1", password="pass12345", email="e@test.com"
        )
        self.seeker = User.objects.create_user(
            username="seeker1", password="pass12345", email="s@test.com"
        )
        self.emp_profile = UserProfile.objects.create(
            user=self.employer_user, role="employer", company_name="Acme"
        )
        UserProfile.objects.create(user=self.seeker, role="jobseeker", email_verified=True)
        from core.services.employer.workspace import WorkspaceService
        workspace = WorkspaceService.auto_create_from_profile(self.emp_profile)
        self.job = Job.objects.create(
            employer=self.emp_profile,
            workspace=workspace,
            title="Python Dev",
            company="Acme",
            description="Python Django REST API",
            location="Remote",
            category="Engineering",
            required_skills=["Python", "Django"],
        )
        self.application = Application.objects.create(
            user=self.seeker, job=self.job, status="Applied"
        )

    def test_valid_pipeline_transition(self):
        from core.hiring.pipeline import PipelineService

        PipelineService.transition(
            self.application, "Screening", updated_by=self.employer_user
        )
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "Screening")
        self.assertTrue(self.application.status_history.exists())

    def test_invalid_pipeline_transition_raises(self):
        from core.hiring.pipeline import PipelineService
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            PipelineService.transition(
                self.application, "Hired", updated_by=self.employer_user
            )

    def test_matching_engine_returns_scores(self):
        from core.ai.matching_engine import MatchingEngineService

        engine = MatchingEngineService()
        result = engine.compute_match(
            self.job.description,
            self.job.category,
            {"skills": ["Python", "Django"], "education": [], "experience": []},
            self.job.required_skills,
        )
        self.assertIn("overall_score", result)
        self.assertGreater(result["overall_score"], 0)


class EmployerPortalTests(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username="emp_portal", password="pass12345", email="emp@test.com"
        )
        self.profile = UserProfile.objects.create(
            user=self.employer, role="employer", company_name="Test Co", email_verified=True
        )
        self.seeker = User.objects.create_user(username="seeker_p", password="pass12345")
        UserProfile.objects.create(user=self.seeker, role="jobseeker", email_verified=True)

    def test_employer_dashboard_requires_employer_role(self):
        self.client.login(username="seeker_p", password="pass12345")
        response = self.client.get(reverse("employer_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_employer_dashboard_loads(self):
        self.client.login(username="emp_portal", password="pass12345")
        response = self.client.get(reverse("employer_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employer/dashboard_v2.html")

    def test_employer_applications_hub(self):
        self.client.login(username="emp_portal", password="pass12345")
        response = self.client.get(reverse("employer_applications"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employer/applications_hub.html")

    def test_legacy_job_applications_redirects(self):
        from core.services.employer.workspace import WorkspaceService
        workspace = WorkspaceService.auto_create_from_profile(self.profile)
        job = Job.objects.create(
            employer=self.profile,
            workspace=workspace,
            title="Dev",
            company="Test Co",
            description="Python",
            location="Remote",
            category="Tech",
        )
        self.client.login(username="emp_portal", password="pass12345")
        response = self.client.get(reverse("job_applications", kwargs={"job_id": job.id}))
        self.assertRedirects(
            response,
            f"{reverse('employer_applications')}?job={job.id}",
        )


class ApplicationWorkflowIntegrationTest(TestCase):
    """End-to-end test: seeker applies → employer sees it everywhere."""

    def setUp(self):
        # Employer
        self.employer_user = User.objects.create_user(
            username="wf_employer", password="pass12345", email="emp@wf.com"
        )
        self.employer_profile = UserProfile.objects.create(
            user=self.employer_user,
            role="employer",
            company_name="WorkflowCo",
            email_verified=True,
        )
        # Job seeker
        self.seeker_user = User.objects.create_user(
            username="wf_seeker", password="pass12345", email="seek@wf.com"
        )
        self.seeker_profile = UserProfile.objects.create(
            user=self.seeker_user, role="jobseeker", email_verified=True
        )
        # Job — employer is UserProfile, NOT User
        from core.services.employer.workspace import WorkspaceService
        workspace = WorkspaceService.auto_create_from_profile(self.employer_profile)
        self.job = Job.objects.create(
            employer=self.employer_profile,
            workspace=workspace,
            title="Workflow Test Dev",
            company="WorkflowCo",
            description="Python Django developer needed with React and SQL skills",
            location="Remote",
            category="Engineering",
            required_skills=["Python", "Django"],
            status="Open",
        )

    # ── 1. Verify Application creation and field linkage ──────────────
    def test_application_created_with_correct_fields(self):
        app = Application.objects.create(
            user=self.seeker_user,
            job=self.job,
            status="Applied",
            qualification="B.Tech CS",
            phone="1234567890",
        )
        app.refresh_from_db()
        self.assertEqual(app.user, self.seeker_user)
        self.assertEqual(app.job, self.job)
        self.assertEqual(app.status, "Applied")
        # Critical: job.employer is a UserProfile, not a User
        self.assertEqual(app.job.employer, self.employer_profile)
        self.assertIsInstance(app.job.employer, UserProfile)

    # ── 2. Verify employer relationship chain ─────────────────────────
    def test_employer_query_chain(self):
        """Employer(UserProfile) → Job → Application — the canonical path."""
        app = Application.objects.create(
            user=self.seeker_user, job=self.job, status="Applied"
        )
        # This is the query pattern used throughout employer views
        found = Application.objects.filter(
            job__employer=self.employer_profile
        )
        self.assertEqual(found.count(), 1)
        self.assertEqual(found.first().id, app.id)

        # WRONG pattern (would fail): filter by User instead of UserProfile
        with self.assertRaises(ValueError):
            Application.objects.filter(
                job__employer=self.employer_user  # type: ignore[arg-type]
            )

    # ── 3. Verify workflow service runs without errors ─────────────────
    def test_workflow_service_creates_artifacts(self):
        from core.models import (
            ApplicationMatchScore,
            ApplicationTimelineEvent,
            Notification,
            ParsedResume,
        )
        from core.hiring.workflow import ApplicationWorkflowService

        app = Application.objects.create(
            user=self.seeker_user, job=self.job, status="Applied"
        )
        ApplicationWorkflowService.process_new_application(app)

        # ParsedResume created (skipped status because no PDF)
        self.assertTrue(ParsedResume.objects.filter(application=app).exists())
        parsed = ParsedResume.objects.get(application=app)
        self.assertIn(parsed.parse_status, ("skipped", "success", "failed"))

        # MatchScore created
        self.assertTrue(ApplicationMatchScore.objects.filter(application=app).exists())
        score = ApplicationMatchScore.objects.get(application=app)
        self.assertGreaterEqual(score.overall_score, 0)

        # Timeline events created (applied + resume_parsed + match_computed)
        events = ApplicationTimelineEvent.objects.filter(application=app)
        event_types = set(events.values_list("event_type", flat=True))
        self.assertIn("applied", event_types)
        self.assertIn("resume_parsed", event_types)
        self.assertIn("match_computed", event_types)

        # Notifications for both employer and seeker
        emp_notifs = Notification.objects.filter(user=self.employer_user)
        self.assertTrue(emp_notifs.exists())
        seeker_notifs = Notification.objects.filter(user=self.seeker_user)
        self.assertTrue(seeker_notifs.exists())

    # ── 4. Employer dashboard shows the application ───────────────────
    def test_employer_dashboard_shows_application(self):
        from core.hiring.workflow import ApplicationWorkflowService

        app = Application.objects.create(
            user=self.seeker_user, job=self.job, status="Applied"
        )
        ApplicationWorkflowService.process_new_application(app)

        self.client.login(username="wf_employer", password="pass12345")
        response = self.client.get(reverse("employer_dashboard"))
        self.assertEqual(response.status_code, 200)

        # Stats should reflect the application
        self.assertEqual(response.context["stats"]["total_applications"], 1)
        # Recent applications should contain our app
        recent = list(response.context["recent_applications"])
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].id, app.id)

    # ── 5. Employer applications hub shows the application ────────────
    def test_employer_applications_hub_shows_application(self):
        from core.hiring.workflow import ApplicationWorkflowService

        app = Application.objects.create(
            user=self.seeker_user, job=self.job, status="Applied"
        )
        ApplicationWorkflowService.process_new_application(app)

        self.client.login(username="wf_employer", password="pass12345")
        response = self.client.get(reverse("employer_applications"))
        self.assertEqual(response.status_code, 200)

        applications = list(response.context["applications"])
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0].id, app.id)
        self.assertEqual(applications[0].user.username, "wf_seeker")
        self.assertEqual(applications[0].job.title, "Workflow Test Dev")
        self.assertEqual(applications[0].status, "Applied")

    # ── 6. Employer applications hub — no status filter hides Applied ─
    def test_hub_no_status_filter_shows_applied(self):
        """Ensure default view (no status filter) includes 'Applied' apps."""
        Application.objects.create(
            user=self.seeker_user, job=self.job, status="Applied"
        )
        self.client.login(username="wf_employer", password="pass12345")
        # No status= param → should show all non-withdrawn
        response = self.client.get(reverse("employer_applications"))
        applications = list(response.context["applications"])
        self.assertEqual(len(applications), 1)

    # ── 7. Employer candidate detail page loads ───────────────────────
    def test_employer_candidate_detail_loads(self):
        from core.hiring.workflow import ApplicationWorkflowService

        app = Application.objects.create(
            user=self.seeker_user, job=self.job, status="Applied"
        )
        ApplicationWorkflowService.process_new_application(app)

        self.client.login(username="wf_employer", password="pass12345")
        response = self.client.get(
            reverse("employer_candidate_detail", kwargs={"app_id": app.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["application"].id, app.id)
        # Match score should be present
        self.assertIsNotNone(response.context["match_score"])

    # ── 8. Employer job detail shows applicant ────────────────────────
    def test_employer_job_detail_shows_applicant(self):
        from core.hiring.workflow import ApplicationWorkflowService

        app = Application.objects.create(
            user=self.seeker_user, job=self.job, status="Applied"
        )
        ApplicationWorkflowService.process_new_application(app)

        self.client.login(username="wf_employer", password="pass12345")
        response = self.client.get(
            reverse("employer_job_detail", kwargs={"job_id": self.job.id})
        )
        self.assertEqual(response.status_code, 200)
        apps = list(response.context["applications"])
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0].user.username, "wf_seeker")

    # ── 9. Job seeker my_applications view shows application ──────────
    def test_seeker_my_applications_shows_app(self):
        app = Application.objects.create(
            user=self.seeker_user, job=self.job, status="Applied"
        )
        self.client.login(username="wf_seeker", password="pass12345")
        response = self.client.get(reverse("my_applications"))
        self.assertEqual(response.status_code, 200)
        applications = list(response.context["applications"])
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0].id, app.id)

    # ── 10. Nulls-last ordering: unscored apps still appear ───────────
    def test_hub_nulls_last_ordering(self):
        """Apps without match scores should still appear, not vanish."""
        # Create app WITHOUT running workflow (so no MatchScore exists)
        app = Application.objects.create(
            user=self.seeker_user, job=self.job, status="Applied"
        )
        self.client.login(username="wf_employer", password="pass12345")
        response = self.client.get(reverse("employer_applications"))
        applications = list(response.context["applications"])
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0].id, app.id)

    # ── 11. apply_job view end-to-end via POST ────────────────────────
    def test_apply_job_view_creates_application(self):
        self.client.login(username="wf_seeker", password="pass12345")
        response = self.client.post(
            reverse("apply_job", kwargs={"job_id": self.job.id}),
            {"qualification": "B.Tech", "phone": "9876543210", "experience": "2 years"},
        )
        # Should redirect to job_detail on success
        self.assertRedirects(response, reverse("job_detail", kwargs={"job_id": self.job.id}))

        # Application should exist in DB
        app = Application.objects.get(user=self.seeker_user, job=self.job)
        self.assertEqual(app.status, "Applied")
        self.assertEqual(app.job.employer, self.employer_profile)

        # Now check employer side
        self.client.logout()
        self.client.login(username="wf_employer", password="pass12345")
        response = self.client.get(reverse("employer_applications"))
        applications = list(response.context["applications"])
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0].user.username, "wf_seeker")
