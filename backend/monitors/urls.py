from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MonitorViewSet

router = DefaultRouter()
router.register(r'', MonitorViewSet, basename='monitor')

urlpatterns = [
    path('', include(router.urls)),
]
