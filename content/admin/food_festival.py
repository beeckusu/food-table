from django.contrib import admin
from content.models import FoodFestival, RestaurantDish


class FoodFestivalDishInline(admin.TabularInline):
    model = RestaurantDish
    fk_name = 'food_festival'
    extra = 0
    fields = ['dish_name', 'restaurant', 'status', 'notes', 'review']
    autocomplete_fields = ['restaurant', 'review']


@admin.register(FoodFestival)
class FoodFestivalAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'country', 'start_date', 'end_date', 'created_at']
    list_filter = ['city', 'country']
    search_fields = ['name', 'city', 'country']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['restaurants']
    inlines = [FoodFestivalDishInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
