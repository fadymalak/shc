from rest_framework import permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Region


class RegionAPIKeyAuthentication(BaseAuthentication):
    """Authentication using region API key"""
    
    def authenticate(self, request):
        api_key = request.META.get('HTTP_AUTHORIZATION', '').replace('Token ', '')
        
        if not api_key:
            return None
        
        try:
            region = Region.objects.get(api_key=api_key, is_active=True)
        except Region.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')
        
        return (region, None)  # Return region as user, None as token


class IsRegionClient(permissions.BasePermission):
    """Permission check for region clients"""
    
    def has_permission(self, request, view):
        return hasattr(request, 'user') and isinstance(request.user, Region)
