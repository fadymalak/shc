from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Incident
from .serializers import IncidentSerializer
from organizations.permissions import IsOrganizationMember


class IncidentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['monitor__name', 'error_message']
    ordering_fields = ['started_at', 'response_time_ms', 'duration_seconds']
    ordering = ['-started_at']

    def get_queryset(self):
        user = self.request.user
        monitor_id = self.request.query_params.get('monitor')
        incident_type = self.request.query_params.get('type')
        status = self.request.query_params.get('status')
        
        queryset = Incident.objects.filter(
            monitor__organization__members__user=user,
            monitor__organization__members__is_active=True
        ).select_related('monitor', 'region', 'monitor__organization').distinct()
        
        if monitor_id:
            queryset = queryset.filter(monitor_id=monitor_id)
        
        if incident_type:
            queryset = queryset.filter(incident_type=incident_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        incident = self.get_object()
        if incident.status == 'open':
            incident.status = 'resolved'
            incident.resolved_at = timezone.now()
            incident.save()
            return Response({'status': 'Incident resolved'})
        return Response({'error': 'Incident already resolved'}, status=400)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get incident statistics"""
        queryset = self.get_queryset()
        
        total_incidents = queryset.count()
        open_incidents = queryset.filter(status='open').count()
        downtime_incidents = queryset.filter(incident_type='downtime').count()
        high_latency_incidents = queryset.filter(incident_type='high_latency').count()
        
        return Response({
            'total': total_incidents,
            'open': open_incidents,
            'resolved': total_incidents - open_incidents,
            'downtime': downtime_incidents,
            'high_latency': high_latency_incidents,
        })
