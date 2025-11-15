from django.db import models
from monitors.models import Monitor
from regions.models import Region


class Incident(models.Model):
    """Incident model - stores only downtime and high latency issues"""
    INCIDENT_TYPE_CHOICES = [
        ('downtime', 'Downtime'),
        ('high_latency', 'High Latency'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
    ]

    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name='incidents')
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, related_name='incidents')
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Incident details
    started_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")
    
    # Response details
    response_time_ms = models.IntegerField(null=True, blank=True, help_text="Response time in milliseconds")
    status_code = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['monitor', 'status', 'started_at']),
            models.Index(fields=['monitor', 'incident_type', 'started_at']),
        ]

    def __str__(self):
        return f"{self.monitor.name} - {self.incident_type} ({self.status})"

    def save(self, *args, **kwargs):
        if self.resolved_at and self.started_at:
            duration = (self.resolved_at - self.started_at).total_seconds()
            self.duration_seconds = int(duration)
        super().save(*args, **kwargs)
