from django.contrib import admin
from content.models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Basic admin interface for Tag model"""
    list_display = ['name', 'slug', 'usage_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'usage_count']
