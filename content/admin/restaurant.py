from django.contrib import admin
from content.models import Restaurant, RestaurantDish


class RestaurantDishInline(admin.TabularInline):
    model = RestaurantDish
    extra = 0
    fields = ['dish_name', 'status', 'source', 'source_detail', 'notes', 'review']
    autocomplete_fields = ['review']


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'province', 'country', 'postal_code', 'visited', 'is_pop_up', 'is_chain', 'created_at']
    list_filter = ['visited', 'is_pop_up', 'city', 'country']
    search_fields = ['name', 'street_address', 'city', 'province', 'country', 'postal_code', 'website']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [RestaurantDishInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RestaurantDish)
class RestaurantDishAdmin(admin.ModelAdmin):
    list_display = ['dish_name', 'restaurant', 'status', 'source', 'created_at']
    list_filter = ['status', 'source']
    search_fields = ['dish_name', 'restaurant__name']
    autocomplete_fields = ['restaurant', 'review']
