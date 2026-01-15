from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "applications"

    def ready(self):
        # Import signal handlers so they are registered
        from . import signals  # noqa: F401