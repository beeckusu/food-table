from django.core.validators import MinValueValidator, MaxValueValidator
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
    excitement = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='How excited you are to try this dish (1-10)',
    )
    notes = models.TextField(blank=True)
    review = models.ForeignKey(
        'Review',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_dish_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    EXCITEMENT_MIN = 1
    EXCITEMENT_MAX = 10
    EXCITEMENT_LEVELS = list(range(EXCITEMENT_MIN, EXCITEMENT_MAX + 1))

    @classmethod
    def is_valid_excitement(cls, value):
        """True for None (unrated) or an int within EXCITEMENT_MIN..EXCITEMENT_MAX."""
        if value is None:
            return True
        return (
            isinstance(value, int) and not isinstance(value, bool)
            and cls.EXCITEMENT_MIN <= value <= cls.EXCITEMENT_MAX
        )

    class Meta:
        ordering = ['dish_name']

    def __str__(self):
        target = self.restaurant.name
        if self.food_festival_id:
            target = f"{target} @ {self.food_festival.name}"
        return f"{self.dish_name} @ {target} ({self.get_status_display()})"
