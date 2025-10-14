from django.contrib import admin
from content.models import Recipe, RecipeTag
from .inlines import ImageInline


class RecipeTagInline(admin.TabularInline):
    """Inline for managing tags attached to recipes"""
    model = RecipeTag
    extra = 1
    fields = ['tag']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin interface for Recipe model"""

    list_display = ['name', 'difficulty', 'total_time_minutes', 'servings', 'created_at']
    list_filter = ['difficulty', 'is_private', 'created_at']
    search_fields = ['name', 'description', 'tips']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'version', 'created_by']
    autocomplete_fields = ['encyclopedia_entry']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Recipe Details', {
            'fields': ('servings', 'prep_time_minutes', 'cook_time_minutes', 'total_time_minutes', 'difficulty')
        }),
        ('Content', {
            'fields': ('ingredients', 'steps', 'tips', 'dietary_restrictions')
        }),
        ('Relationships', {
            'fields': ('encyclopedia_entry',)
        }),
        ('Privacy', {
            'fields': ('is_private',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'version', 'metadata'),
            'classes': ('collapse',)
        }),
    )

    inlines = [RecipeTagInline, ImageInline]

    def save_model(self, request, obj, form, change):
        """Auto-populate created_by from request.user on first save"""
        if not change:  # Only set on creation, not on update
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
