from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import StatusPage
from .serializers import StatusPageSerializer, PublicStatusPageSerializer
from organizations.permissions import IsOrganizationMember, IsOrganizationOwnerOrLead
from incidents.models import Incident


class StatusPageViewSet(viewsets.ModelViewSet):
    serializer_class = StatusPageSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        user = self.request.user
        return StatusPage.objects.filter(
            organization__members__user=user,
            organization__members__is_active=True
        ).select_related('organization').prefetch_related('monitors')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOrganizationOwnerOrLead()]
        return super().get_permissions()

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def public(self, request, pk=None):
        """Public endpoint for status page"""
        status_page = get_object_or_404(StatusPage, pk=pk, is_public=True)
        serializer = PublicStatusPageSerializer(status_page)
        
        # Get recent incidents for monitors on this status page
        monitor_ids = status_page.monitors.values_list('id', flat=True)
        incidents = Incident.objects.filter(
            monitor_id__in=monitor_ids
        ).order_by('-started_at')[:50]
        
        from incidents.serializers import IncidentSerializer
        incidents_data = IncidentSerializer(incidents, many=True).data
        
        # Calculate uptime percentages
        uptime_data = {}
        for monitor in status_page.monitors.all():
            total_incidents = Incident.objects.filter(monitor=monitor).count()
            downtime_incidents = Incident.objects.filter(
                monitor=monitor,
                incident_type='downtime'
            ).count()
            # Simple calculation - in production, use actual uptime tracking
            uptime_percentage = max(0, 100 - (downtime_incidents * 0.1))
            uptime_data[monitor.id] = round(uptime_percentage, 2)
        
        response_data = serializer.data
        response_data['incidents'] = incidents_data
        response_data['uptime_percentages'] = uptime_data
        
        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='by-subdomain/(?P<subdomain>[^/.]+)')
    def by_subdomain(self, request, subdomain=None):
        """Get status page by subdomain (public endpoint)"""
        status_page = get_object_or_404(StatusPage, subdomain=subdomain, is_public=True)
        return self.public(request, pk=status_page.pk)
