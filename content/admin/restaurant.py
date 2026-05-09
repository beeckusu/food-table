from django.contrib import admin
from content.models import Restaurant


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'province', 'country', 'postal_code', 'created_at']
    list_filter = ['city', 'country']
    search_fields = ['name', 'street_address', 'city', 'province', 'country', 'postal_code']
    readonly_fields = ['created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
