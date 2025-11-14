from django.db import models
from organizations.models import Organization
from regions.models import Region


class Monitor(models.Model):
    """Monitor model for tracking different types of checks"""
    CHECK_TYPE_CHOICES = [
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
        ('dns', 'DNS'),
        ('tcp', 'TCP'),
        ('custom', 'Custom (Word Check)'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='monitors')
    name = models.CharField(max_length=255)
    check_type = models.CharField(max_length=20, choices=CHECK_TYPE_CHOICES)
    target = models.CharField(max_length=500, help_text="URL, domain, or IP address to monitor")
    
    # HTTP/HTTPS specific fields
    expected_status_code = models.IntegerField(default=200, null=True, blank=True)
    expected_keyword = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="For custom check type - word that should exist in response"
    )
    
    # DNS specific fields
    expected_dns_record = models.CharField(max_length=255, null=True, blank=True)
    dns_record_type = models.CharField(max_length=10, default='A', null=True, blank=True)
    
    # Check settings
    check_interval = models.IntegerField(default=60, help_text="Interval in seconds")
    timeout = models.IntegerField(default=30, help_text="Timeout in seconds")
    high_latency_threshold = models.IntegerField(
        default=5000, 
        help_text="Latency threshold in milliseconds to trigger incident"
    )
    
    # Regions to check from
    regions = models.ManyToManyField(Region, related_name='monitors', blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_paused = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'organizations.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_monitors'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.check_type})"

    def clean(self):
        """Validate monitor configuration based on check type"""
        from django.core.exceptions import ValidationError
        
        if self.check_type == 'custom' and not self.expected_keyword:
            raise ValidationError("Expected keyword is required for custom check type")
        
        if self.check_type == 'dns' and not self.expected_dns_record:
            raise ValidationError("Expected DNS record is required for DNS check type")
