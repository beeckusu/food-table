from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from content.models import Encyclopedia
from .inlines import ImageInline, EncyclopediaTagInline


@admin.register(Encyclopedia)
class EncyclopediaAdmin(admin.ModelAdmin):
    """Admin interface for Encyclopedia model"""

    list_display = ['name', 'placeholder_status', 'parent', 'cuisine_type', 'created_at']
    list_filter = ['is_placeholder', 'cuisine_type', 'dish_category', 'region']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'version']
    actions = ['mark_as_placeholder', 'mark_as_complete']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'is_placeholder'),
            'description': 'Core entry information. Check "Is placeholder" to create a minimal stub entry.'
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

    def placeholder_status(self, obj):
        """Display placeholder status with visual indicator"""
        if obj.is_placeholder:
            if obj.description:
                return format_html(
                    '<span style="color: #f59e0b;">⚠️ Placeholder (has description)</span>'
                )
            return format_html(
                '<span style="color: #dc2626;">📝 Placeholder</span>'
            )
        return format_html('<span style="color: #10b981;">✓ Complete</span>')

    placeholder_status.short_description = 'Status'
    placeholder_status.admin_order_field = 'is_placeholder'

    def mark_as_placeholder(self, request, queryset):
        """Admin action to mark selected entries as placeholders"""
        updated = queryset.update(is_placeholder=True)
        self.message_user(request, f'{updated} entry(ies) marked as placeholder.')

    mark_as_placeholder.short_description = 'Mark selected entries as placeholder'

    def mark_as_complete(self, request, queryset):
        """Admin action to mark selected entries as complete"""
        updated = queryset.update(is_placeholder=False)
        self.message_user(request, f'{updated} entry(ies) marked as complete.')

    mark_as_complete.short_description = 'Mark selected entries as complete'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize the parent dropdown to show existing entries"""
        if db_field.name == "parent":
            kwargs["queryset"] = Encyclopedia.objects.all().order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """Customize form to add help text for is_placeholder field"""
        form = super().get_form(request, obj, **kwargs)
        if 'is_placeholder' in form.base_fields:
            form.base_fields['is_placeholder'].help_text = (
                'Check this box to create a placeholder entry with minimal information. '
                'Placeholder entries can have empty descriptions and are useful for noting '
                'similar dishes that need full content later.'
            )

        # Check if converting from placeholder
        if obj and obj.is_placeholder and request.GET.get('from_placeholder') == 'true':
            messages.info(
                request,
                f'Converting placeholder: "{obj.name}". Add a description to complete the conversion. '
                f'All existing relationships will be preserved.'
            )
            form.base_fields['description'].help_text = (
                '⚠️ Required to complete placeholder conversion. '
                'Provide a detailed description of this dish.'
            )

        return form

    def save_model(self, request, obj, form, change):
        """
        Override save to automatically convert placeholders to full entries
        when description is added.
        """
        # Check if this was a placeholder that now has a description
        was_placeholder = False
        if change and obj.pk:
            # Get the original object from database
            try:
                original = Encyclopedia.objects.get(pk=obj.pk)
                was_placeholder = original.is_placeholder
            except Encyclopedia.DoesNotExist:
                pass

        # Auto-convert placeholder to full entry if description is added
        if was_placeholder and obj.description and obj.description.strip():
            obj.is_placeholder = False
            messages.success(
                request,
                f'Placeholder "{obj.name}" successfully converted to full entry!'
            )

        # Set created_by if creating a new object
        if not change and not obj.created_by:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    class Media:
        css = {
            'all': (
                'admin/css/encyclopedia_placeholder.css',
                'admin/css/encyclopedia_quick_create.css',
            )
        }
        js = (
            'admin/js/encyclopedia_placeholder.js',
            'admin/js/encyclopedia_quick_create.js',
        )
