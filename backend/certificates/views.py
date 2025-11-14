from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Certificate
from .serializers import CertificateSerializer
from organizations.permissions import IsOrganizationMember


class CertificateViewSet(viewsets.ModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        user = self.request.user
        domain = self.request.query_params.get('domain')
        expiring_soon = self.request.query_params.get('expiring_soon')
        
        queryset = Certificate.objects.filter(
            monitor__organization__members__user=user,
            monitor__organization__members__is_active=True
        ).select_related('monitor', 'monitor__organization').distinct()
        
        if domain:
            queryset = queryset.filter(domain__icontains=domain)
        
        if expiring_soon == 'true':
            queryset = queryset.filter(is_expiring_soon=True, is_valid=True)
        
        return queryset

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get certificates expiring soon"""
        queryset = self.get_queryset().filter(is_expiring_soon=True, is_valid=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_notification_sent(self, request, pk=None):
        """Mark notification as sent"""
        certificate = self.get_object()
        certificate.notification_sent = True
        certificate.last_notification_sent_at = timezone.now()
        certificate.save()
        return Response({'status': 'Notification marked as sent'})
