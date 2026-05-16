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
    dish_name = models.CharField(max_length=255)
    encyclopedia_entry = models.ForeignKey(
        'Encyclopedia',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_dishes'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WISHLIST)
    source = models.CharField(max_length=255, blank=True)
    source_detail = models.CharField(max_length=255, blank=True)
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
        return f"{self.dish_name} @ {self.restaurant.name} ({self.get_status_display()})"
