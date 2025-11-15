from django.contrib import admin
from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = [
        'monitor', 'incident_type', 'status', 'region', 
        'started_at', 'resolved_at', 'response_time_ms'
    ]
    list_filter = ['incident_type', 'status', 'started_at', 'monitor__organization']
    search_fields = ['monitor__name', 'error_message']
    readonly_fields = ['duration_seconds', 'created_at', 'updated_at']
    date_hierarchy = 'started_at'
