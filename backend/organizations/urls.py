from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, OrganizationMemberViewSet, register, login

router = DefaultRouter()
router.register(r'', OrganizationViewSet, basename='organization')
router.register(r'members', OrganizationMemberViewSet, basename='organization-member')

urlpatterns = [
    path('', include(router.urls)),
]
