from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver


class FoodFestival(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    website = models.URLField(max_length=500, blank=True, default='')
    restaurants = models.ManyToManyField(
        'Restaurant',
        related_name='food_festivals',
        blank=True,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_festivals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='content_foodfestival_name_idx'),
        ]

    def __str__(self):
        parts = [self.name]
        if self.city:
            parts.append(self.city)
        if self.country:
            parts.append(self.country)
        return ', '.join(parts) if len(parts) > 1 else self.name


@receiver(post_save, sender=FoodFestival)
def update_food_festival_search_vector(sender, instance, **kwargs):
    """
    Signal handler to automatically update search_vector field when FoodFestival is saved.
    """
    if kwargs.get('update_fields') and 'search_vector' in kwargs['update_fields']:
        return

    FoodFestival.objects.filter(pk=instance.pk).update(
        search_vector=(
            SearchVector('name', weight='A')
            + SearchVector('city', weight='B')
            + SearchVector('country', weight='C')
        )
    )
