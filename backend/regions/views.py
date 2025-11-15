from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Region
from .serializers import RegionSerializer
from .permissions import RegionAPIKeyAuthentication, IsRegionClient
from organizations.permissions import IsOrganizationMember, IsOrganizationOwnerOrLead
from monitors.models import Monitor
from monitors.serializers import MonitorSerializer
from incidents.models import Incident


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

    @action(detail=False, methods=['get'], url_path='(?P<region_code>[^/.]+)/monitors',
            authentication_classes=[RegionAPIKeyAuthentication],
            permission_classes=[IsRegionClient])
    def monitors_by_code(self, request, region_code=None):
        """Get monitors assigned to this region (for region clients)"""
        try:
            region = Region.objects.get(code=region_code, is_active=True)
            
            # Verify the region matches the authenticated region
            if request.user != region:
                return Response(
                    {'error': 'Region code does not match authenticated region'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            monitors = Monitor.objects.filter(
                regions=region,
                is_active=True,
                is_paused=False
            ).select_related('organization', 'created_by').prefetch_related('regions')
            
            serializer = MonitorSerializer(monitors, many=True, context={'request': request})
            return Response(serializer.data)
        except Region.DoesNotExist:
            return Response(
                {'error': 'Region not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['POST'])
@authentication_classes([RegionAPIKeyAuthentication])
@permission_classes([IsRegionClient])
def submit_check_result(request, region_code):
    """Submit check result from region client"""
    try:
        region = Region.objects.get(code=region_code, is_active=True)
        
        # Verify the region matches the authenticated region
        if request.user != region:
            return Response(
                {'error': 'Region code does not match authenticated region'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        monitor_id = request.data.get('monitor_id')
        status_value = request.data.get('status')
        response_time_ms = request.data.get('response_time_ms')
        status_code = request.data.get('status_code')
        error_message = request.data.get('error_message')
        incident_type = request.data.get('incident_type')
        
        if not monitor_id:
            return Response(
                {'error': 'monitor_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            monitor = Monitor.objects.get(id=monitor_id, regions=region)
        except Monitor.DoesNotExist:
            return Response(
                {'error': 'Monitor not found or not assigned to this region'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only create incident if there's downtime or high latency
        if incident_type:
            # Check if there's already an open incident of this type
            existing_incident = Incident.objects.filter(
                monitor=monitor,
                region=region,
                incident_type=incident_type,
                status='open'
            ).first()
            
            if existing_incident:
                # Update existing incident
                existing_incident.response_time_ms = response_time_ms
                existing_incident.status_code = status_code
                existing_incident.error_message = error_message
                existing_incident.save()
            else:
                # Create new incident
                Incident.objects.create(
                    monitor=monitor,
                    region=region,
                    incident_type=incident_type,
                    status='open',
                    started_at=timezone.now(),
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                    error_message=error_message,
                )
        
        return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
        
    except Region.DoesNotExist:
        return Response(
            {'error': 'Region not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
