from django.db import models
from django.contrib.auth.models import User
from .encyclopedia import Encyclopedia


class EncyclopediaVersion(models.Model):
    """
    Version history model for Encyclopedia entries.
    Stores snapshots of encyclopedia entries at specific points in time.
    """
    # Foreign Keys
    encyclopedia = models.ForeignKey(
        Encyclopedia,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version = models.IntegerField()

    # Snapshot Fields
    name = models.CharField(max_length=255)
    description = models.TextField()
    parent_id = models.IntegerField(null=True, blank=True)
    cuisine_type = models.CharField(max_length=100, blank=True, null=True)
    dish_category = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    metadata_snapshot = models.JSONField(default=dict, blank=True)

    # Audit Fields
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='encyclopedia_version_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    change_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['encyclopedia', 'version']
        ordering = ['-version']
        verbose_name = 'Encyclopedia Version'
        verbose_name_plural = 'Encyclopedia Versions'

    def __str__(self):
        return f"{self.encyclopedia.name} v{self.version}"
