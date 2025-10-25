from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericRelation
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
        related_name='dish_reviews',
        null=True,
        blank=True,
        help_text="Optional link to encyclopedia entry (can be set manually after import)"
    )
    dish_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Dish name as parsed from import (used when encyclopedia_entry is not linked)"
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
    notes = models.TextField(
        blank=True,
        help_text="Optional notes for this specific dish"
    )

    # GenericRelation for images
    images = GenericRelation('Image')

    class Meta:
        ordering = ['review', 'id']
        verbose_name = 'Review Dish'
        verbose_name_plural = 'Review Dishes'

    def __str__(self):
        if self.encyclopedia_entry:
            dish_display = self.encyclopedia_entry.name
        elif self.dish_name:
            dish_display = self.dish_name
        else:
            dish_display = "Unlinked Dish"
        return f"{self.review} - {dish_display}"


@receiver(post_save, sender=ReviewDish)
def update_review_search_on_dish_save(sender, instance, **kwargs):
    """
    When a ReviewDish is saved, trigger the Review's search vector update.
    """
    # Trigger the Review's post_save signal to update its search vector
    instance.review.save(update_fields=['updated_at'])


@receiver(post_delete, sender=ReviewDish)
def update_review_search_on_dish_delete(sender, instance, **kwargs):
    """
    When a ReviewDish is deleted, trigger the Review's search vector update.
    """
    # Trigger the Review's post_save signal to update its search vector
    instance.review.save(update_fields=['updated_at'])
