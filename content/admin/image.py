from django.contrib import admin
from content.models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    """Basic admin interface for Image model"""
    list_display = ['id', 'caption', 'content_type', 'object_id', 'uploaded_at']
    list_filter = ['content_type', 'uploaded_at']
    search_fields = ['caption', 'alt_text']
    readonly_fields = ['uploaded_at']
