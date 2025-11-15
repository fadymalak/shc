from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegionViewSet, submit_check_result

router = DefaultRouter()
router.register(r'', RegionViewSet, basename='region')

urlpatterns = [
    path('', include(router.urls)),
    path('<str:region_code>/check-results/', submit_check_result, name='region-check-results'),
]
