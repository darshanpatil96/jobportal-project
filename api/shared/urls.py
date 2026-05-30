from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="api_register"),
    path("me/", views.CurrentUserView.as_view(), name="api_current_user"),
    path("notifications/", views.NotificationListView.as_view(), name="api_notifications"),
]
