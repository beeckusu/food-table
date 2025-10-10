from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .review import Review
from .encyclopedia import Encyclopedia


class ReviewDish(models.Model):
    """
    Junction table linking Reviews to Encyclopedia entries (dishes).
    Allows one review to reference multiple dishes with optional per-dish ratings and costs.
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='review_dishes'
    )
    encyclopedia_entry = models.ForeignKey(
        Encyclopedia,
        on_delete=models.CASCADE,
        related_name='dish_reviews'
    )
    dish_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Optional rating for this specific dish (0-100)"
    )
    cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional cost/price for this dish"
    )

    class Meta:
        unique_together = ['review', 'encyclopedia_entry']
        ordering = ['review', 'encyclopedia_entry']
        verbose_name = 'Review Dish'
        verbose_name_plural = 'Review Dishes'

    def __str__(self):
        return f"{self.review} - {self.encyclopedia_entry.name}"
