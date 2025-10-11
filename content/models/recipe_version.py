from django.db import models
from django.contrib.auth.models import User
from .recipe import Recipe


class RecipeVersion(models.Model):
    """
    Version history model for Recipe entries.
    Stores snapshots of recipe entries at specific points in time.
    """
    # Foreign Keys
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version = models.IntegerField()

    # Snapshot Fields
    name = models.CharField(max_length=255)
    description = models.TextField()
    servings = models.PositiveIntegerField(null=True, blank=True)
    prep_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    cook_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    difficulty = models.CharField(max_length=10)
    ingredients_snapshot = models.JSONField(default=list, blank=True)
    steps_snapshot = models.JSONField(default=list, blank=True)
    tips = models.TextField(blank=True)

    # Audit Fields
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recipe_version_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    change_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['recipe', 'version']
        ordering = ['-version']
        verbose_name = 'Recipe Version'
        verbose_name_plural = 'Recipe Versions'

    def __str__(self):
        return f"{self.recipe.name} v{self.version}"
