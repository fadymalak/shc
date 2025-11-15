from django.contrib import admin
from .models import Monitor


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'check_type', 'target', 'is_active', 'is_paused', 'created_at']
    list_filter = ['check_type', 'is_active', 'is_paused', 'created_at']
    search_fields = ['name', 'target', 'organization__name']
    filter_horizontal = ['regions']
