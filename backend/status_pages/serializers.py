from rest_framework import serializers
from .models import StatusPage
from monitors.serializers import MonitorSerializer


class StatusPageSerializer(serializers.ModelSerializer):
    monitors = MonitorSerializer(many=True, read_only=True)
    monitor_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=None,
        write_only=True,
        required=False,
        source='monitors'
    )
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_slug = serializers.SlugField(source='organization.slug', read_only=True)

    class Meta:
        model = StatusPage
        fields = [
            'id', 'organization', 'organization_name', 'organization_slug',
            'title', 'description', 'subdomain', 'custom_domain', 'logo_url',
            'theme_color', 'monitors', 'monitor_ids', 'show_historical_incidents',
            'show_uptime_percentage', 'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request'):
            user = self.context['request'].user
            from monitors.models import Monitor
            self.fields['monitor_ids'].queryset = Monitor.objects.filter(
                organization__members__user=user,
                organization__members__is_active=True
            ).distinct()


class PublicStatusPageSerializer(serializers.ModelSerializer):
    """Serializer for public status page view"""
    monitors = MonitorSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = StatusPage
        fields = [
            'title', 'description', 'organization_name', 'logo_url',
            'theme_color', 'monitors', 'show_historical_incidents',
            'show_uptime_percentage'
        ]
