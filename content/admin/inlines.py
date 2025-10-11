from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib import admin
from content.models import Image, EncyclopediaTag


class ImageInline(GenericTabularInline):
    """Inline for managing images attached to encyclopedia entries"""
    model = Image
    extra = 1
    fields = ['image', 'caption', 'alt_text', 'order']
    ordering = ['order']


class EncyclopediaTagInline(admin.TabularInline):
    """Inline for managing tags attached to encyclopedia entries"""
    model = EncyclopediaTag
    extra = 1
    fields = ['tag']
