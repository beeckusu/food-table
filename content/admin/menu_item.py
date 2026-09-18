from django.contrib import admin
from content.models import MenuItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """Admin interface for MenuItem model"""

    list_display = ['name', 'restaurant', 'encyclopedia_entry', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'restaurant__name']
    autocomplete_fields = ['restaurant', 'encyclopedia_entry']
