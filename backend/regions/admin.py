from django.contrib import admin
from .models import Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'location', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'organization']
    search_fields = ['name', 'code', 'location', 'organization__name']
