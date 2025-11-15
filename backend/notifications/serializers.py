from rest_framework import serializers
from .models import NotificationChannel, MonitorNotificationPreference, NotificationLog
from monitors.serializers import MonitorSerializer


class NotificationChannelSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'organization', 'organization_name', 'channel_type', 'name', 'is_active',
            'slack_webhook_url', 'slack_channel', 'teams_webhook_url', 'email_addresses',
            'notify_on_downtime', 'notify_on_high_latency', 'notify_on_resolution',
            'created_at', 'updated_at', 'created_by', 'created_by_email'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
        extra_kwargs = {
            'slack_webhook_url': {'write_only': True},
            'teams_webhook_url': {'write_only': True},
        }

    def validate(self, attrs):
        channel_type = attrs.get('channel_type', self.instance.channel_type if self.instance else None)
        
        if channel_type == 'slack' and not attrs.get('slack_webhook_url'):
            raise serializers.ValidationError({
                'slack_webhook_url': 'Slack webhook URL is required for Slack channels'
            })
        
        if channel_type == 'teams' and not attrs.get('teams_webhook_url'):
            raise serializers.ValidationError({
                'teams_webhook_url': 'Microsoft Teams webhook URL is required for Teams channels'
            })
        
        if channel_type == 'email' and not attrs.get('email_addresses'):
            raise serializers.ValidationError({
                'email_addresses': 'Email addresses are required for email channels'
            })
        
        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class MonitorNotificationPreferenceSerializer(serializers.ModelSerializer):
    monitor = MonitorSerializer(read_only=True)
    monitor_id = serializers.IntegerField(write_only=True)
    channel = NotificationChannelSerializer(read_only=True)
    channel_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MonitorNotificationPreference
        fields = [
            'id', 'monitor', 'monitor_id', 'channel', 'channel_id',
            'is_enabled', 'notify_on_downtime', 'notify_on_high_latency', 'notify_on_resolution'
        ]


class NotificationLogSerializer(serializers.ModelSerializer):
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    monitor_name = serializers.CharField(source='monitor.name', read_only=True)

    class Meta:
        model = NotificationLog
        fields = [
            'id', 'channel', 'channel_name', 'monitor', 'monitor_name',
            'incident', 'notification_type', 'status', 'error_message',
            'sent_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
