from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericRelation
from .review import Review
from .menu_item import MenuItem


class ReviewDish(models.Model):
    """
    Junction table linking Reviews to MenuItems (dishes at a specific restaurant).
    Allows one review to reference multiple dishes with optional per-dish ratings and costs.
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='review_dishes'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name='review_dishes',
        help_text="The restaurant-scoped dish being reviewed, shared with every other review of it."
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
        return f"{self.review} - {self.dish_name}"

    @property
    def dish_name(self):
        """The dish's name, read through its MenuItem (the single source of truth)."""
        return self.menu_item.name

    @property
    def encyclopedia_entry(self):
        """The encyclopedia entry linked to this dish's MenuItem, if any."""
        return self.menu_item.encyclopedia_entry

    @encyclopedia_entry.setter
    def encyclopedia_entry(self, value):
        # Written through to the MenuItem (not this row) so every review sharing
        # the same dish picks up the link, per FT-192.
        self.menu_item.encyclopedia_entry = value
        self.menu_item.save(update_fields=['encyclopedia_entry'])

    @property
    def restaurant(self):
        """The restaurant this dish was tried at (from its MenuItem)."""
        return self.menu_item.restaurant


@receiver(post_save, sender=ReviewDish)
def update_review_search_on_dish_save(sender, instance, **kwargs):
    """
    When a ReviewDish is saved, trigger the Review's search vector update
    and recalculate overall rating if it's set to auto-calculate.
    """
    review = instance.review

    # Only recalculate if the rating is set to auto-calculate
    if review.metadata.get('rating_auto_calculated', False):
        new_rating = review._calculate_rating_from_dishes()

        # Only update if rating has changed
        if review.rating != new_rating:
            review.rating = new_rating
            review.save(update_fields=['rating', 'updated_at'])
        else:
            # Just trigger search vector update
            review.save(update_fields=['updated_at'])
    else:
        # Just trigger search vector update
        review.save(update_fields=['updated_at'])


@receiver(post_delete, sender=ReviewDish)
def update_review_search_on_dish_delete(sender, instance, **kwargs):
    """
    When a ReviewDish is deleted, trigger the Review's search vector update
    and recalculate overall rating if it's set to auto-calculate.
    """
    review = instance.review

    # Only recalculate if the rating is set to auto-calculate
    if review.metadata.get('rating_auto_calculated', False):
        new_rating = review._calculate_rating_from_dishes()

        # Only update if rating has changed
        if review.rating != new_rating:
            review.rating = new_rating
            review.save(update_fields=['rating', 'updated_at'])
        else:
            # Just trigger search vector update
            review.save(update_fields=['updated_at'])
    else:
        # Just trigger search vector update
        review.save(update_fields=['updated_at'])
