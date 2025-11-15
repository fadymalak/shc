from django.db import models
from organizations.models import Organization
from monitors.models import Monitor


class StatusPage(models.Model):
    """Status page model for public-facing status pages"""
    organization = models.OneToOneField(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='status_page'
    )
    title = models.CharField(max_length=255, default="Status Page")
    description = models.TextField(blank=True)
    subdomain = models.SlugField(
        unique=True,
        help_text="Subdomain for the status page (e.g., 'status' for status.yourdomain.com)"
    )
    
    # Customization
    custom_domain = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="Custom domain for status page (e.g., status.yourdomain.com)"
    )
    logo_url = models.URLField(null=True, blank=True)
    theme_color = models.CharField(max_length=7, default="#0066CC", help_text="Hex color code")
    
    # Monitors to display
    monitors = models.ManyToManyField(Monitor, related_name='status_pages', blank=True)
    
    # Settings
    show_historical_incidents = models.BooleanField(default=True)
    show_uptime_percentage = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.name} - {self.subdomain}"
