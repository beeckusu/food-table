from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
import logging

logger = logging.getLogger(__name__)

_ADDRESS_FIELDS = ('street_address', 'city', 'province', 'country', 'postal_code')


class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    google_place_id = models.CharField(max_length=255, blank=True, default='')
    is_pop_up = models.BooleanField(default=False)
    website = models.URLField(max_length=500, blank=True, default='')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurants'
    )
    visited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        unique_together = [('name', 'street_address')]
        indexes = [
            models.Index(fields=['name'], name='content_restaurant_name_idx'),
        ]

    def __str__(self):
        parts = [self.name]
        if self.city:
            parts.append(self.city)
        if self.country:
            parts.append(self.country)
        return ', '.join(parts) if len(parts) > 1 else self.name

    @property
    def chain_locations(self):
        """Other Restaurant rows sharing this name, i.e. other locations of the same chain."""
        if not self.name:
            return Restaurant.objects.none()
        return Restaurant.objects.filter(name=self.name).exclude(pk=self.pk)

    @property
    def is_chain(self):
        return self.chain_locations.exists()

    def _geocode(self):
        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
        if not api_key:
            return
        address = ', '.join(
            p for p in [self.street_address, self.city, self.province, self.country, self.postal_code]
            if p
        )
        if not address:
            return
        try:
            response = requests.get(
                'https://maps.googleapis.com/maps/api/geocode/json',
                params={'address': address, 'key': api_key},
                timeout=5,
            )
            data = response.json()
            if data.get('status') == 'OK':
                loc = data['results'][0]['geometry']['location']
                self.latitude = loc['lat']
                self.longitude = loc['lng']
        except Exception:
            logger.exception('Geocoding failed for restaurant %s', self.name)

    def save(self, *args, **kwargs):
        if not self.is_pop_up:
            needs_coords = self.latitude is None or self.longitude is None
            address_changed = False
            if self.pk:
                try:
                    old = Restaurant.objects.get(pk=self.pk)
                    address_changed = any(
                        getattr(old, f) != getattr(self, f) for f in _ADDRESS_FIELDS
                    )
                except Restaurant.DoesNotExist:
                    address_changed = True
            else:
                address_changed = True
            if needs_coords or address_changed:
                self._geocode()
        super().save(*args, **kwargs)


@receiver(post_save, sender=Restaurant)
def update_restaurant_search_vector(sender, instance, **kwargs):
    """
    Signal handler to automatically update search_vector field when Restaurant is saved.
    Updates the search vector with name (primary) and location fields (secondary).
    """
    # Avoid infinite recursion by checking if we're already updating
    if kwargs.get('update_fields') and 'search_vector' in kwargs['update_fields']:
        return

    Restaurant.objects.filter(pk=instance.pk).update(
        search_vector=(
            SearchVector('name', weight='A')
            + SearchVector('city', weight='B')
            + SearchVector('street_address', weight='B')
            + SearchVector('province', weight='C')
            + SearchVector('country', weight='C')
        )
    )
