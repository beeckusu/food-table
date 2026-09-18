from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core.management import call_command
from django.contrib import messages
from content.models import Restaurant, Review, ReviewDish, ReviewTag, Image
from .inlines import ImageInline


class DishImageInline(GenericTabularInline):
    """Inline for managing images attached to dishes"""
    model = Image
    extra = 1
    fields = ['image', 'caption', 'alt_text', 'order']
    ordering = ['order']


class ReviewDishInline(admin.TabularInline):
    """Inline for managing dishes attached to reviews"""
    model = ReviewDish
    extra = 1
    fields = ['menu_item', 'dish_rating', 'cost', 'notes']
    autocomplete_fields = ['menu_item']


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

    list_display = ['get_restaurant_name', 'visit_date', 'rating', 'is_draft', 'created_at']
    list_filter = ['rating', 'is_draft', 'visit_date', 'restaurant__city', 'restaurant__country']
    search_fields = ['restaurant__name', 'restaurant__city', 'restaurant__country', 'food_festival__name', 'notes']
    date_hierarchy = 'visit_date'
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    autocomplete_fields = ['restaurant', 'food_festival']
    actions = ['import_reviews_from_confluence']

    fieldsets = (
        ('Restaurant', {
            'fields': ('restaurant', 'food_festival')
        }),
        ('Visit Details', {
            'fields': ('visit_date', 'entry_time', 'party_size')
        }),
        ('Rating and Notes', {
            'fields': ('rating', 'notes', 'title')
        }),
        ('Privacy', {
            'fields': ('is_private', 'is_draft')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'metadata'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Restaurant', ordering='restaurant__name')
    def get_restaurant_name(self, obj):
        if obj.restaurant_id:
            return obj.restaurant.name
        if obj.food_festival_id:
            return f'{obj.food_festival.name} (festival)'
        return '—'

    inlines = [ReviewDishInline, ImageInline, ReviewTagInline]

    def save_model(self, request, obj, form, change):
        """Auto-populate created_by from request.user on first save"""
        if not change:  # Only set on creation, not on update
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReviewDish)
class ReviewDishAdmin(admin.ModelAdmin):
    """Admin interface for ReviewDish model"""

    list_display = ['dish_name', 'review', 'dish_rating', 'cost']
    list_filter = ['dish_rating', 'review__visit_date']
    search_fields = ['menu_item__name', 'notes', 'review__restaurant__name']
    autocomplete_fields = ['menu_item', 'review']

    fieldsets = (
        ('Dish Information', {
            'fields': ('review', 'menu_item')
        }),
        ('Rating and Cost', {
            'fields': ('dish_rating', 'cost')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )

    inlines = [DishImageInline]
