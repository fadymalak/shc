from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    """Organization model for grouping users and monitors"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text="Used for status page subdomain")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class OrganizationMember(models.Model):
    """Model for organization membership with roles"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('project_lead', 'Project Lead'),
        ('developer', 'Developer'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['organization', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"

    def has_permission(self, permission_type):
        """Check if member has permission based on role"""
        permissions = {
            'owner': ['view', 'edit', 'delete', 'manage_members', 'manage_settings'],
            'project_lead': ['view', 'edit', 'manage_members'],
            'developer': ['view'],
        }
        return permission_type in permissions.get(self.role, [])
