from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StatusPageViewSet

router = DefaultRouter()
router.register(r'', StatusPageViewSet, basename='status-page')

urlpatterns = [
    path('', include(router.urls)),
]
