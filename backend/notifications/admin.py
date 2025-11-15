from django.contrib import admin
from .models import NotificationChannel, MonitorNotificationPreference, NotificationLog


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'channel_type', 'is_active', 'created_at']
    list_filter = ['channel_type', 'is_active', 'created_at', 'organization']
    search_fields = ['name', 'organization__name', 'email_addresses']
    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'channel_type', 'name', 'is_active')
        }),
        ('Slack Configuration', {
            'fields': ('slack_webhook_url', 'slack_channel'),
            'classes': ('collapse',)
        }),
        ('Microsoft Teams Configuration', {
            'fields': ('teams_webhook_url',),
            'classes': ('collapse',)
        }),
        ('Email Configuration', {
            'fields': ('email_addresses',),
            'classes': ('collapse',)
        }),
        ('Notification Preferences', {
            'fields': ('notify_on_downtime', 'notify_on_high_latency', 'notify_on_resolution')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MonitorNotificationPreference)
class MonitorNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['monitor', 'channel', 'is_enabled', 'notify_on_downtime', 'notify_on_high_latency']
    list_filter = ['is_enabled', 'channel__channel_type']
    search_fields = ['monitor__name', 'channel__name']


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['channel', 'monitor', 'notification_type', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'notification_type', 'channel__channel_type', 'created_at']
    search_fields = ['channel__name', 'monitor__name', 'error_message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
