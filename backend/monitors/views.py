from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Monitor
from .serializers import MonitorSerializer
from organizations.permissions import IsOrganizationMember, IsOrganizationOwnerOrLead


class MonitorViewSet(viewsets.ModelViewSet):
    serializer_class = MonitorSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        user = self.request.user
        org_id = self.request.query_params.get('organization')
        
        queryset = Monitor.objects.filter(
            organization__members__user=user,
            organization__members__is_active=True
        ).distinct()
        
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        return queryset.select_related('organization', 'created_by').prefetch_related('regions')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOrganizationOwnerOrLead()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        monitor = self.get_object()
        monitor.is_paused = True
        monitor.save()
        return Response({'status': 'Monitor paused'})

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        monitor = self.get_object()
        monitor.is_paused = False
        monitor.save()
        return Response({'status': 'Monitor resumed'})
