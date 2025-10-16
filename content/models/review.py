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
