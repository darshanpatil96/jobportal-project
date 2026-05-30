"""
Django signals for hiring pipeline side effects.

Primary business logic lives in hiring/ services; signals provide
automatic hooks when models are saved outside service layer (e.g. admin).
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from core.models import Application, ApplicationStatusHistory
from core.hiring.timeline import TimelineService


@receiver(pre_save, sender=Application)
def cache_application_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Application.objects.only("status").get(pk=instance.pk)
            instance._old_status = old.status
        except Application.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Application)
def application_status_history_fallback(sender, instance, created, **kwargs):
    """Fallback history when status changed outside PipelineService (e.g. admin)."""
    if created:
        return
    old_status = getattr(instance, "_old_status", None)
    if not old_status or old_status == instance.status:
        return
    if ApplicationStatusHistory.objects.filter(
        application=instance,
        old_status=Application.normalize_status(old_status),
        new_status=Application.normalize_status(instance.status),
    ).exists():
        return
    ApplicationStatusHistory.objects.create(
        application=instance,
        old_status=Application.normalize_status(old_status),
        new_status=Application.normalize_status(instance.status),
        updated_by=None,
        notes="Updated outside pipeline service",
    )
    TimelineService.log_status_changed(
        instance,
        Application.normalize_status(old_status),
        Application.normalize_status(instance.status),
        None,
    )
