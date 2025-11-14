from rest_framework import serializers
from .models import Incident
from monitors.serializers import MonitorSerializer
from regions.serializers import RegionSerializer


class IncidentSerializer(serializers.ModelSerializer):
    monitor = MonitorSerializer(read_only=True)
    monitor_id = serializers.IntegerField(write_only=True, required=False)
    region = RegionSerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    monitor_name = serializers.CharField(source='monitor.name', read_only=True)
    organization_name = serializers.CharField(source='monitor.organization.name', read_only=True)

    class Meta:
        model = Incident
        fields = [
            'id', 'monitor', 'monitor_id', 'monitor_name', 'organization_name',
            'region', 'region_id', 'incident_type', 'status', 'started_at',
            'resolved_at', 'duration_seconds', 'response_time_ms', 'status_code',
            'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'duration_seconds']
