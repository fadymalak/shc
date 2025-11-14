"""
URL configuration for uptime_monitor project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from organizations.views import register, login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('rest_framework.urls')),
    path('api/auth/register/', register, name='register'),
    path('api/auth/login/', login, name='login'),
    path('api/organizations/', include('organizations.urls')),
    path('api/monitors/', include('monitors.urls')),
    path('api/incidents/', include('incidents.urls')),
    path('api/status-pages/', include('status_pages.urls')),
    path('api/regions/', include('regions.urls')),
    path('api/certificates/', include('certificates.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
