from pathlib import Path
import os
from importlib import reload

from django.conf import settings
from django.test import SimpleTestCase


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
