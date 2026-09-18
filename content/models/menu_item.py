from django.db import models


class MenuItem(models.Model):
    """
    A dish as offered by a specific restaurant. Every ReviewDish that reviews
    the same dish at the same restaurant shares one MenuItem, so repeat
    reviews consolidate onto a single encyclopedia entry instead of each
    review creating its own disconnected dish record (FT-192).
    """
    restaurant = models.ForeignKey(
        'Restaurant',
        on_delete=models.CASCADE,
        related_name='menu_items'
    )
    name = models.CharField(max_length=255)
    name_key = models.CharField(max_length=255, editable=False, db_index=True)
    encyclopedia_entry = models.ForeignKey(
        'Encyclopedia',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='menu_items'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = [('restaurant', 'name_key')]
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'

    def __str__(self):
        return f"{self.name} @ {self.restaurant.name}"

    def save(self, *args, **kwargs):
        self.name_key = self.name.strip().lower()
        super().save(*args, **kwargs)
