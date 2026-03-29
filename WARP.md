# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Environment & setup

- Python/Django project rooted at this directory.
- Django settings module: `jobportal.settings` (already configured in `manage.py` and `render.yaml`).
- Local development uses SQLite by default; production (Render) can override `DATABASE_URL` via `dj-database-url`.
- Configuration is read from environment variables via `python-decouple` and a `.env` file (see `.env.example`). At minimum set:
  - `SECRET_KEY`
  - `DEBUG` (`True` for local dev, `False` for production)
  - `ALLOWED_HOSTS` (comma-separated)
  - Optionally `CSRF_TRUSTED_ORIGINS` for hosted environments.

Typical local setup (PowerShell on Windows):

```bash path=null start=null
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
```

## Core commands

All commands are expected to run from the project root (where `manage.py` lives).

- Run development server
  - `python manage.py runserver`
- Apply database migrations
  - `python manage.py migrate`
- Create a superuser for admin access
  - `python manage.py createsuperuser`
- Collect static files (for a production-like build)
  - `python manage.py collectstatic --noinput`
- Open a Django shell
  - `python manage.py shell`

### Tests

Tests live under `applications/tests.py` (and can be expanded per app).

- Run all tests
  - `python manage.py test`
- Run tests for a specific app
  - `python manage.py test applications`
- Run a single test case or method (example using the existing class in `applications/tests.py`)
  - Entire test class:
    - `python manage.py test applications.tests.RequirementsAndRenderTests`
  - Single test method:
    - `python manage.py test applications.tests.RequirementsAndRenderTests.test_requirements_ignore_commented_windows_only_packages`

### Render deployment

Deployment to Render is configured via `render.yaml`:

- Build step (what Render runs on deploy):
  - `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- Start command (production server):
  - `gunicorn jobportal.wsgi:application`

## High-level architecture

### Project layout

- `jobportal/` – Django project configuration (settings, root URLs, WSGI/ASGI).
- `accounts/` – User accounts, profiles, roles, authentication views, in-app notifications, and a global context processor.
- `jobs/` – Core job board features: job listings, search/filtering, dashboards, company views, saved jobs, and public pages (home, about, companies).
- `applications/` – Job application model, forms, and signals for email + in-app notifications.
- `templates/` – HTML templates (shared `base.html`, dashboards, detail/list views for jobs, accounts, and applications).
- `static/` and `media/` – Static assets and user-uploaded files.

### Settings and configuration (`jobportal/settings.py`)

- Uses `python-decouple` (`config()`) to pull secrets and deployment settings from environment variables.
- Database is configured via `dj-database-url.config`, defaulting to an SQLite file under `BASE_DIR` for development; on Render or other hosts, `DATABASE_URL` can point to PostgreSQL.
- Installed apps include the three local apps: `accounts`, `applications.apps.ApplicationsConfig`, and `jobs`.
- Templates are configured to use `BASE_DIR / "templates"` plus per-app templates. A custom context processor `accounts.context_processors.notifications` injects `unread_notification_count` into all templates for the logged-in user.
- Static files:
  - `STATIC_URL = '/static/'`
  - `STATICFILES_DIRS = [BASE_DIR / 'static']`
  - `STATIC_ROOT = BASE_DIR / 'staticfiles'` (used by `collectstatic` and production hosting).
  - WhiteNoise (`whitenoise.middleware.WhiteNoiseMiddleware` and `CompressedManifestStaticFilesStorage`) serves static files in production.
- Media uploads:
  - `MEDIA_URL = '/media/'`, `MEDIA_ROOT = BASE_DIR / 'media'`.
- Email backend is set to console for development (`django.core.mail.backends.console.EmailBackend`) with `DEFAULT_FROM_EMAIL = 'noreply@jobportal.local'`.

### URL routing and request flow

- Root URLConf: `jobportal/urls.py`.
  - `''` → `jobs.views.home` (landing page showing latest jobs, categories, and job types).
  - `'accounts/'` → `accounts.urls` (registration, login, profile, notifications, and Django auth views like password reset).
  - `'jobs/'` → `jobs.urls` (job board features and dashboards).
- When `DEBUG` is `True`, media files under `MEDIA_ROOT` are served via `django.conf.urls.static.static`.

### Accounts app: users, profiles, roles, and notifications

**Models (`accounts/models.py`)**

- `UserProfile` extends `django.contrib.auth.models.User` via a `OneToOneField` and adds:
  - `role` (`jobseeker` or `employer`), used heavily across views to gate access.
  - Personal info: `full_name`, `phone`, `location`, `resume`.
  - Employer-specific fields: `company_name`, `company_website`, `company_logo`, `company_description`.
  - `email_verified` flag, set after activation via an emailed token.
- `Notification` model stores simple in-app messages for users (with `is_read` and timestamp ordering).

**Forms (`accounts/forms.py`)**

- `UserRegisterForm` wraps `UserCreationForm`, adds an email field and role selection, and ensures a `UserProfile` is created/updated with the chosen role on save.
- `UserProfileForm` allows editing both personal and employer-specific fields, including file uploads.

**Views (`accounts/views.py`)**

- `register_user` handles registration with `UserRegisterForm`, creates the user, and sends an activation email containing a tokenized link (`activate_account`).
- `activate_account` decodes `uidb64` + token, marks `UserProfile.email_verified = True`, and redirects the user to login.
- `login_user` uses Django's `AuthenticationForm` and redirects based on `UserProfile.role`:
  - Employers → `employer_dashboard` (jobs app).
  - Jobseekers → `jobseeker_dashboard` (jobs app).
- `profile_detail` / `profile_edit` show and edit the `UserProfile` for the logged-in user.
- `notifications_list` shows a feed of in-app `Notification` instances and marks them all read when visited.

**Context processor (`accounts/context_processors.py`)**

- Adds `unread_notification_count` to every template for authenticated users. This depends on the `Notification` model and is wired into `TEMPLATES[...]['OPTIONS']['context_processors']` in `settings.py`.

**URLs (`accounts/urls.py`)**

- Routes `accounts/` paths to custom views:
  - `login/`, `register/`, `profile/`, `profile/edit/`, `notifications/`, and `activate/<uidb64>/<token>/`.
- Includes Django's built-in auth URLs (password reset, logout, etc.) at the same prefix via `include('django.contrib.auth.urls')`.

### Applications app: job applications and notification signals

**Model (`applications/models.py`)**

- `Application` links `User` and `Job`:
  - Fields include `cover_letter`, `resume`, `qualification`, `phone`, `experience`, `status`, and `applied_at`.
  - `STATUS_CHOICES` track the lifecycle (`Applied`, `Under Review`, `Shortlisted`, `Interview`, `Rejected`, `Hired`, `Withdrawn`).
  - A `UniqueConstraint` on `(user, job)` ensures one active application per user per job.

**Form (`applications/forms.py`)**

- `ApplicationForm` exposes the candidate-facing fields and enforces `qualification` and `phone` as required at the form level; provides Tailwind-style CSS classes and HTML attributes suitable for the templates.

**Signals (`applications/signals.py`)**

- Connected via `ApplicationsConfig.ready()` in `applications/apps.py`.
- `pre_save` handler `store_old_status` caches the pre-update status on the `Application` instance (`_old_status`) so the `post_save` handler can detect real changes without extra queries.
- Helper functions:
  - `_notify_employer_new_application` sends an email to the employer for a new `Application` and creates an in-app `Notification` for the employer.
  - `_notify_candidate_status_change` sends an email plus in-app `Notification` to the candidate when their application status changes.
- `application_post_save` orchestrates behaviour:
  - On create: notifies the employer and also creates a confirmation `Notification` for the candidate.
  - On update: if status changed compared to `_old_status`, triggers `_notify_candidate_status_change`.

### Jobs app: job listings, dashboards, companies, and saved jobs

**Models (`jobs/models.py`)**

- `Job` represents a job posting and is owned by an employer `UserProfile`:
  - Includes `title`, `company`, `description`, `location`, `salary`, `category`, `job_type`, `status`, and timestamp (`posted_at`).
  - `job_type` (e.g., `Full-Time`, `Part-Time`, `Internship`, `Remote`) and `status` (`Open`, `Closed`, `Draft`) drive filtering and dashboard views.
- `SavedJob` links `User` to `Job` as a bookmark, enforced by a `unique_together` constraint; ordered by `created_at`.

**Views (`jobs/views.py`) – key flows**

- `jobseeker_dashboard`:
  - Restricted to `role == 'jobseeker'` (employers are redirected to `employer_dashboard`).
  - Builds simple recommendations based on categories and job types from the user's previous `Application` records.
  - Aggregates recent applications, saved jobs, and total counts.
- `job_list`:
  - Main search/filter page for open jobs.
  - Supports query text, location, category, job_type, and quick filters (`remote_only`, `internships_only`, `entry_level_only`).
  - Provides multiple sort options (`newest`, `salary`, and by application count).
  - Annotates each job with application counts and tracks which jobs are saved/applied for the current user.
- `job_detail` and `apply_job`:
  - Show a single job and whether the current user has applied/saved it.
  - `apply_job` requires login and a verified email (`UserProfile.email_verified`), prevents duplicate applications, and uses `ApplicationForm` to capture candidate data.
- `employer_dashboard`:
  - Restricted to `role == 'employer'` only.
  - Segments the employer's jobs into Open, Closed, and Draft lists, each annotated with application counts.
  - Computes simple analytics (jobs per month, applications per job/category).
- `job_applications`:
  - Employer-only view to manage applications for a specific job.
  - Allows updating the `Application.status` for each candidate (excluding `Withdrawn`) and uses the shared `STATUS_CHOICES` from the `Application` model.
- CRUD for jobs (`create_job`, `edit_job`, `delete_job`):
  - All restricted to employers; job creation additionally requires `email_verified`.
- Public/company views and utilities:
  - `home` – landing page summarising latest jobs and categories.
  - `companies` / `company_detail` – list employers with non-empty `company_name` and show their open jobs.
  - `about` – static about page.
  - `my_applications` – jobseeker view of their own applications, with sorting.
  - `toggle_save_job` and `saved_jobs` – manage and display saved jobs for the logged-in user, using the `SavedJob` model.

**URLs (`jobs/urls.py`)**

- Exposes routes under `/jobs/` for dashboards, list/detail, application editing/withdrawal, employer management, saved jobs, and static pages.

### Tests and deployment safeguards

- `applications/tests.py` currently focuses on deployment-related tests:
  - Validates that Windows-only packages remain commented out in `requirements.txt`.
  - Ensures the WSGI application can be imported and initialised in a Render-like environment (with `RENDER` env var set) without requiring Windows-only dependencies.
- When adding new tests, follow Django's standard testing patterns within each app and run them via `python manage.py test` or app-specific invocations as described above.
