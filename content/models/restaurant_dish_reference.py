from django.db import models


class RestaurantDishReference(models.Model):
    dish = models.ForeignKey(
        'RestaurantDish',
        on_delete=models.CASCADE,
        related_name='references'
    )
    source = models.CharField(max_length=255, blank=True)
    source_detail = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['pk']
