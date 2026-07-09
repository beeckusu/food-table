from django.db import models
from .restaurant import Restaurant


class RestaurantDish(models.Model):
    STATUS_HAD = 'had'
    STATUS_WISHLIST = 'wishlist'
    STATUS_CHOICES = [
        (STATUS_HAD, 'Had'),
        (STATUS_WISHLIST, 'Wishlist'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='dishes'
    )
    food_festival = models.ForeignKey(
        'FoodFestival',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='dishes',
        help_text='Set when this dish was tried at the restaurant as part of a food festival',
    )
    dish_name = models.CharField(max_length=255)
    encyclopedia_entry = models.ForeignKey(
        'Encyclopedia',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_dishes'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WISHLIST)
    notes = models.TextField(blank=True)
    review = models.ForeignKey(
        'Review',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_dish_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['dish_name']

    def __str__(self):
        target = self.restaurant.name
        if self.food_festival_id:
            target = f"{target} @ {self.food_festival.name}"
        return f"{self.dish_name} @ {target} ({self.get_status_display()})"
