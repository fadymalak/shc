from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Region
from .serializers import RegionSerializer
from organizations.permissions import IsOrganizationMember, IsOrganizationOwnerOrLead


class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        user = self.request.user
        org_id = self.request.query_params.get('organization')
        
        queryset = Region.objects.filter(
            organization__members__user=user,
            organization__members__is_active=True
        ).distinct()
        
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        return queryset.select_related('organization')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOrganizationOwnerOrLead()]
        return super().get_permissions()
