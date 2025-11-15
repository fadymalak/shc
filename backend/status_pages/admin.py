from django.contrib import admin
from .models import StatusPage


@admin.register(StatusPage)
class StatusPageAdmin(admin.ModelAdmin):
    list_display = ['organization', 'title', 'subdomain', 'custom_domain', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['organization__name', 'subdomain', 'custom_domain', 'title']
    filter_horizontal = ['monitors']
