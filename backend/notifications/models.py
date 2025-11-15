from django.db import models
from organizations.models import Organization, User
from monitors.models import Monitor


class NotificationChannel(models.Model):
    """Notification channel configuration"""
    CHANNEL_TYPES = [
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('email', 'Email'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notification_channels')
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    name = models.CharField(max_length=255, help_text="Friendly name for this channel")
    is_active = models.BooleanField(default=True)
    
    # Slack configuration
    slack_webhook_url = models.URLField(null=True, blank=True, help_text="Slack webhook URL")
    slack_channel = models.CharField(max_length=100, null=True, blank=True, help_text="Slack channel name")
    
    # Microsoft Teams configuration
    teams_webhook_url = models.URLField(null=True, blank=True, help_text="Microsoft Teams webhook URL")
    
    # Email configuration
    email_addresses = models.TextField(
        null=True, 
        blank=True,
        help_text="Comma-separated list of email addresses"
    )
    
    # Notification preferences
    notify_on_downtime = models.BooleanField(default=True)
    notify_on_high_latency = models.BooleanField(default=True)
    notify_on_resolution = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_channels')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.name} - {self.get_channel_type_display()} ({self.name})"

    def clean(self):
        """Validate channel configuration"""
        from django.core.exceptions import ValidationError
        
        if self.channel_type == 'slack' and not self.slack_webhook_url:
            raise ValidationError("Slack webhook URL is required for Slack channels")
        
        if self.channel_type == 'teams' and not self.teams_webhook_url:
            raise ValidationError("Microsoft Teams webhook URL is required for Teams channels")
        
        if self.channel_type == 'email' and not self.email_addresses:
            raise ValidationError("Email addresses are required for email channels")


class MonitorNotificationPreference(models.Model):
    """Notification preferences for specific monitors"""
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name='notification_preferences')
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE, related_name='monitor_preferences')
    is_enabled = models.BooleanField(default=True)
    notify_on_downtime = models.BooleanField(default=True)
    notify_on_high_latency = models.BooleanField(default=True)
    notify_on_resolution = models.BooleanField(default=True)

    class Meta:
        unique_together = ['monitor', 'channel']

    def __str__(self):
        return f"{self.monitor.name} -> {self.channel.name}"


class NotificationLog(models.Model):
    """Log of sent notifications"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE, related_name='logs')
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name='notification_logs', null=True)
    incident = models.ForeignKey('incidents.Incident', on_delete=models.SET_NULL, null=True, related_name='notifications')
    notification_type = models.CharField(max_length=50)  # 'downtime', 'high_latency', 'resolved'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['channel', 'status', 'created_at']),
            models.Index(fields=['monitor', 'created_at']),
        ]

    def __str__(self):
        return f"{self.channel.name} - {self.notification_type} - {self.status}"
