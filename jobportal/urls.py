from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from jobs import views


urlpatterns = [
    path('admin/', admin.site.urls),

    # Home Page
    path('', views.home, name='home'),

    # Include app URLs
    path('accounts/', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
