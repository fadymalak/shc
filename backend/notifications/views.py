from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import NotificationChannel, MonitorNotificationPreference, NotificationLog
from .serializers import (
    NotificationChannelSerializer,
    MonitorNotificationPreferenceSerializer,
    NotificationLogSerializer
)
from organizations.permissions import IsOrganizationMember, IsOrganizationOwnerOrLead
from .tasks import send_notification


class NotificationChannelViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        user = self.request.user
        org_id = self.request.query_params.get('organization')
        
        queryset = NotificationChannel.objects.filter(
            organization__members__user=user,
            organization__members__is_active=True
        ).distinct()
        
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        return queryset.select_related('organization', 'created_by')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOrganizationOwnerOrLead()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test notification channel"""
        channel = self.get_object()
        
        # Get a monitor from the organization for testing
        monitor = channel.organization.monitors.first()
        if not monitor:
            return Response(
                {'error': 'No monitors found in organization for testing'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send test notification
        send_notification.delay(
            channel.id,
            monitor.id,
            None,
            'downtime'  # Test with downtime notification
        )
        
        return Response({'status': 'Test notification sent'})


class MonitorNotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = MonitorNotificationPreferenceSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        user = self.request.user
        monitor_id = self.request.query_params.get('monitor')
        channel_id = self.request.query_params.get('channel')
        
        queryset = MonitorNotificationPreference.objects.filter(
            monitor__organization__members__user=user,
            monitor__organization__members__is_active=True
        ).select_related('monitor', 'channel').distinct()
        
        if monitor_id:
            queryset = queryset.filter(monitor_id=monitor_id)
        
        if channel_id:
            queryset = queryset.filter(channel_id=channel_id)
        
        return queryset


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        user = self.request.user
        channel_id = self.request.query_params.get('channel')
        monitor_id = self.request.query_params.get('monitor')
        status_filter = self.request.query_params.get('status')
        
        queryset = NotificationLog.objects.filter(
            channel__organization__members__user=user,
            channel__organization__members__is_active=True
        ).select_related('channel', 'monitor', 'incident').distinct()
        
        if channel_id:
            queryset = queryset.filter(channel_id=channel_id)
        
        if monitor_id:
            queryset = queryset.filter(monitor_id=monitor_id)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
