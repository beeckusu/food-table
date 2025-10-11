from django.contrib import admin
from content.models import Encyclopedia
from .inlines import ImageInline, EncyclopediaTagInline


@admin.register(Encyclopedia)
class EncyclopediaAdmin(admin.ModelAdmin):
    """Admin interface for Encyclopedia model"""

    list_display = ['name', 'parent', 'cuisine_type', 'created_at']
    list_filter = ['cuisine_type', 'dish_category', 'region']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'version']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Hierarchy', {
            'fields': ('parent',)
        }),
        ('Classification', {
            'fields': ('cuisine_type', 'dish_category', 'region')
        }),
        ('Content', {
            'fields': ('cultural_significance', 'popular_examples', 'history', 'similar_dishes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'version', 'metadata'),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ['similar_dishes']
    inlines = [ImageInline, EncyclopediaTagInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize the parent dropdown to show existing entries"""
        if db_field.name == "parent":
            kwargs["queryset"] = Encyclopedia.objects.all().order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
