from django.db import models
from organizations.models import Organization


class Region(models.Model):
    """Region model for tracking monitors from different geographic locations"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='regions')
    name = models.CharField(max_length=100, help_text="e.g., US-East, EU-West, Asia-Pacific")
    code = models.CharField(max_length=50, unique=True, help_text="Unique region code")
    location = models.CharField(max_length=255, help_text="City, Country")
    client_endpoint = models.URLField(
        help_text="Endpoint URL of the custom client deployed in this region"
    )
    api_key = models.CharField(
        max_length=255,
        help_text="API key for authenticating with the region client"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['organization', 'code']

    def __str__(self):
        return f"{self.name} ({self.code})"
