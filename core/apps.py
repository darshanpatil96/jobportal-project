from django.contrib.admin.apps import AdminConfig


class CoreConfig(AdminConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Job Portal"
