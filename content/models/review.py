from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.search import SearchVectorField
from django.contrib.contenttypes.fields import GenericRelation


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
