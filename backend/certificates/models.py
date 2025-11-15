from django.db import models
from django.utils import timezone
from monitors.models import Monitor


class Certificate(models.Model):
    """TLS Certificate tracking model"""
    monitor = models.ForeignKey(
        Monitor, 
        on_delete=models.CASCADE, 
        related_name='certificates',
        null=True,
        blank=True,
        help_text="Optional: Link to a monitor"
    )
    domain = models.CharField(max_length=255, help_text="Domain name for the certificate")
    
    # Certificate details
    issuer = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=255, blank=True)
    
    # Validity dates
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField()
    
    # Status
    is_valid = models.BooleanField(default=True)
    days_until_expiry = models.IntegerField(null=True, blank=True)
    is_expiring_soon = models.BooleanField(default=False)
    
    # Notification tracking
    notification_sent = models.BooleanField(default=False)
    last_notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    last_checked_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['valid_until']
        indexes = [
            models.Index(fields=['domain', 'valid_until']),
            models.Index(fields=['is_expiring_soon', 'notification_sent']),
        ]

    def __str__(self):
        return f"{self.domain} - Expires: {self.valid_until}"

    def save(self, *args, **kwargs):
        if self.valid_until:
            now = timezone.now()
            if self.valid_until < now:
                self.is_valid = False
                self.days_until_expiry = 0
            else:
                delta = self.valid_until - now
                self.days_until_expiry = delta.days
                
                # Check if expiring soon (default 30 days, configurable)
                from django.conf import settings
                warning_days = getattr(settings, 'CERTIFICATE_EXPIRY_WARNING_DAYS', 30)
                self.is_expiring_soon = self.days_until_expiry <= warning_days and self.days_until_expiry > 0
        
        super().save(*args, **kwargs)

    @property
    def needs_notification(self):
        """Check if certificate needs notification"""
        from django.conf import settings
        warning_days = getattr(settings, 'CERTIFICATE_EXPIRY_WARNING_DAYS', 30)
        
        return (
            self.is_expiring_soon and
            self.is_valid and
            (not self.notification_sent or 
             (self.last_notification_sent_at and 
              (timezone.now() - self.last_notification_sent_at).days >= 7))  # Re-notify weekly
        )
