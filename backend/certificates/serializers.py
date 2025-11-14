from rest_framework import serializers
from .models import Certificate
from monitors.serializers import MonitorSerializer


class CertificateSerializer(serializers.ModelSerializer):
    monitor = MonitorSerializer(read_only=True)
    monitor_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    monitor_name = serializers.CharField(source='monitor.name', read_only=True)

    class Meta:
        model = Certificate
        fields = [
            'id', 'monitor', 'monitor_id', 'monitor_name', 'domain',
            'issuer', 'subject', 'serial_number', 'valid_from', 'valid_until',
            'is_valid', 'days_until_expiry', 'is_expiring_soon',
            'notification_sent', 'last_notification_sent_at',
            'last_checked_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'days_until_expiry', 'is_expiring_soon', 'created_at', 
            'updated_at', 'last_checked_at'
        ]
