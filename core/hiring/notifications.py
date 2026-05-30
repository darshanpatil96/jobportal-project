from core.models import Notification


class NotificationService:
    """Centralized in-app notification creation."""

    @staticmethod
    def notify(user, message: str) -> Notification:
        return Notification.objects.create(user=user, message=message[:255])

    @staticmethod
    def notify_many(users, message: str):
        return [
            NotificationService.notify(user, message) for user in users if user
        ]
