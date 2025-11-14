from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = [
        'domain', 'monitor', 'valid_until', 'days_until_expiry', 
        'is_valid', 'is_expiring_soon', 'notification_sent', 'last_checked_at'
    ]
    list_filter = ['is_valid', 'is_expiring_soon', 'notification_sent', 'last_checked_at']
    search_fields = ['domain', 'issuer', 'subject']
    readonly_fields = ['days_until_expiry', 'created_at', 'updated_at', 'last_checked_at']
    date_hierarchy = 'valid_until'
