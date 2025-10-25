from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core.management import call_command
from django.contrib import messages
from content.models import Review, ReviewDish, ReviewTag, Image
from .inlines import ImageInline


class ReviewDishInline(admin.TabularInline):
    """Inline for managing dishes attached to reviews"""
    model = ReviewDish
    extra = 1
    fields = ['dish_name', 'encyclopedia_entry', 'dish_rating', 'cost', 'notes']
    autocomplete_fields = ['encyclopedia_entry']


class ReviewTagInline(admin.TabularInline):
    """Inline for managing tags attached to reviews"""
    model = ReviewTag
    extra = 1
    fields = ['tag']


def import_reviews_from_confluence(modeladmin, request, queryset):
    """
    Admin action to import restaurant reviews from Confluence export JSON.
    Note: This action ignores the selected queryset and imports from the JSON file.
    """
    try:
        # Call the management command
        call_command('import_confluence_reviews', '--json-file', 'confluence_reviews_export.json')
        messages.success(request, 'Successfully imported reviews from Confluence. Check the console for details.')
    except Exception as e:
        messages.error(request, f'Error importing reviews: {str(e)}')

import_reviews_from_confluence.short_description = "Import reviews from Confluence export JSON"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for Review model"""

    list_display = ['restaurant_name', 'visit_date', 'rating', 'created_at']
    list_filter = ['rating', 'visit_date', 'location']
    search_fields = ['restaurant_name', 'location', 'notes']
    date_hierarchy = 'visit_date'
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    actions = ['import_reviews_from_confluence']

    fieldsets = (
        ('Restaurant Information', {
            'fields': ('restaurant_name', 'location', 'address')
        }),
        ('Visit Details', {
            'fields': ('visit_date', 'entry_time', 'party_size')
        }),
        ('Rating and Notes', {
            'fields': ('rating', 'notes', 'title')
        }),
        ('Privacy', {
            'fields': ('is_private',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'metadata'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ReviewDishInline, ImageInline, ReviewTagInline]

    def save_model(self, request, obj, form, change):
        """Auto-populate created_by from request.user on first save"""
        if not change:  # Only set on creation, not on update
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
