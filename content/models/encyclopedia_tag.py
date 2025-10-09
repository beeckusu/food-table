from django.db import models
from .encyclopedia import Encyclopedia


class EncyclopediaTag(models.Model):
    """
    Junction table for Encyclopedia and Tag relationship.
    """
    encyclopedia = models.ForeignKey(Encyclopedia, on_delete=models.CASCADE, related_name='encyclopedia_tags')
    tag = models.CharField(max_length=100)  # Simple tag as string for now
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['encyclopedia', 'tag']
        ordering = ['tag']
        verbose_name = 'Encyclopedia Tag'
        verbose_name_plural = 'Encyclopedia Tags'

    def __str__(self):
        return f"{self.encyclopedia.name} - {self.tag}"
