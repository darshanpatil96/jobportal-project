from accounts.models import Notification


def notifications(request):
    """
    Context processor to add unread notification count to all templates
    """
    if request.user.is_authenticated:
        unread_notification_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    else:
        unread_notification_count = 0
    
    return {
        'unread_notification_count': unread_notification_count,
    }
