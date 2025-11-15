from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationChannelViewSet,
    MonitorNotificationPreferenceViewSet,
    NotificationLogViewSet
)

router = DefaultRouter()
router.register(r'channels', NotificationChannelViewSet, basename='notification-channel')
router.register(r'preferences', MonitorNotificationPreferenceViewSet, basename='notification-preference')
router.register(r'logs', NotificationLogViewSet, basename='notification-log')

urlpatterns = [
    path('', include(router.urls)),
]
