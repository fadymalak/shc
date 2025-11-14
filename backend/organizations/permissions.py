from rest_framework import permissions


class IsOrganizationMember(permissions.BasePermission):
    """Check if user is a member of the organization"""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            org = obj.organization
        elif isinstance(obj, type) and hasattr(obj, '_meta'):
            # For queryset filtering
            return True
        else:
            org = obj

        return org.members.filter(user=request.user, is_active=True).exists()


class IsOrganizationOwnerOrLead(permissions.BasePermission):
    """Check if user is owner or project lead of the organization"""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            org = obj.organization
        else:
            org = obj

        member = org.members.filter(user=request.user, is_active=True).first()
        if not member:
            return False
        return member.role in ['owner', 'project_lead']


class IsOrganizationOwner(permissions.BasePermission):
    """Check if user is owner of the organization"""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            org = obj.organization
        else:
            org = obj

        member = org.members.filter(user=request.user, is_active=True).first()
        if not member:
            return False
        return member.role == 'owner'
