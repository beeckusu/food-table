from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models.signals import post_save
from django.dispatch import receiver


class Review(models.Model):
    """
    Review model for storing restaurant visit reviews.
    """
    # Core Identity Fields
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    restaurant_name = models.CharField(max_length=255)

    # Visit Information
    visit_date = models.DateField()
    entry_time = models.TimeField(help_text="Time of entry to the restaurant")
    party_size = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of people in the party"
    )

    # Location Information
    location = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)

    # Rating and Content
    rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall restaurant rating (0-100)"
    )
    notes = models.TextField(blank=True)

    # Metadata Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviews'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_private = models.BooleanField(default=False)

    # Extensibility and Search
    metadata = models.JSONField(default=dict, blank=True)
    search_vector = SearchVectorField(null=True, blank=True)

    # GenericRelation for images
    images = GenericRelation('Image')

    class Meta:
        ordering = ['-visit_date', '-entry_time']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        indexes = [
            models.Index(fields=['-visit_date']),
            models.Index(fields=['restaurant_name']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        if self.title:
            return f"{self.title} - {self.restaurant_name}"
        return f"{self.restaurant_name} ({self.visit_date})"

    def save(self, *args, **kwargs):
        """
        Override save to auto-calculate overall rating from dish ratings when not provided.
        """
        # Auto-calculate rating if not provided (None, 0, or empty)
        if not self.rating:
            # If this is a new instance, we can't access related dishes yet
            # So we need to save first, then update the rating
            is_new = self.pk is None

            if is_new:
                # For new reviews, use default neutral rating
                # It will be recalculated after dishes are added
                self.rating = 50
                # Mark as auto-calculated
                self.metadata['rating_auto_calculated'] = True
            else:
                # For existing reviews, calculate from current dish ratings
                self.rating = self._calculate_rating_from_dishes()
                # Mark as auto-calculated
                self.metadata['rating_auto_calculated'] = True

        super().save(*args, **kwargs)

    def _calculate_rating_from_dishes(self):
        """
        Calculate overall rating as the average of all dish ratings.

        Returns:
            int: Average rating (0-100), or 50 if no rated dishes exist
        """
        # Get all dish ratings that are not None
        dish_ratings = self.review_dishes.filter(
            dish_rating__isnull=False
        ).values_list('dish_rating', flat=True)

        if dish_ratings:
            # Calculate average and round to nearest integer
            return round(sum(dish_ratings) / len(dish_ratings))

        # Default to neutral rating if no rated dishes
        return 50

    def get_display_image(self):
        """
        Get the best image to display for this review.

        Priority:
        1. First review-level image (if available)
        2. First image from highest-rated dish (if available)
        3. None (if no images exist anywhere)

        Returns:
            Image instance or None
        """
        # Try review-level image first
        review_image = self.images.first()
        if review_image:
            return review_image

        # Fall back to highest-rated dish image
        highest_rated_dish = self.review_dishes.filter(
            dish_rating__isnull=False,
            images__isnull=False
        ).order_by('-dish_rating').first()

        if highest_rated_dish:
            return highest_rated_dish.images.first()

        return None


@receiver(post_save, sender=Review)
def update_review_search_vector(sender, instance, **kwargs):
    """
    Signal handler to automatically update search_vector field when Review is saved.
    Updates the search vector with restaurant_name, title, notes, and related dish information.
    """
    # Avoid infinite recursion by checking if we're already updating
    if kwargs.get('update_fields') and 'search_vector' in kwargs['update_fields']:
        return

    # Build search vector with restaurant_name (A), title (B), and notes (C)
    search_vector_expr = SearchVector('restaurant_name', weight='A')

    # Add title if it exists
    if instance.title:
        search_vector_expr = search_vector_expr + SearchVector('title', weight='B')

    # Add notes if they exist
    if instance.notes:
        search_vector_expr = search_vector_expr + SearchVector('notes', weight='C')

    # Collect dish names and notes from related ReviewDish entries
    dish_text_parts = []
    for review_dish in instance.review_dishes.select_related('encyclopedia_entry').all():
        # Add dish name
        if review_dish.encyclopedia_entry:
            dish_text_parts.append(review_dish.encyclopedia_entry.name)
        # Add dish-specific notes
        if review_dish.notes:
            dish_text_parts.append(review_dish.notes)

    # Combine all dish-related text
    dish_text = ' '.join(dish_text_parts)

    # If there's dish text, add it to the search vector with weight D
    if dish_text:
        from django.contrib.postgres.search import SearchVector as SV
        # Use raw SQL to include the dish text in search vector
        Review.objects.filter(pk=instance.pk).update(
            search_vector=search_vector_expr + SV(models.Value(dish_text), weight='D')
        )
    else:
        # Update search_vector without dish text
        Review.objects.filter(pk=instance.pk).update(search_vector=search_vector_expr)
