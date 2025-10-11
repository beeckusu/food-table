from django.db import models
from .recipe import Recipe
from .tag import Tag


class RecipeTag(models.Model):
    """
    Junction table for Recipe and Tag relationship.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_tags'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='recipe_tags'
    )

    class Meta:
        unique_together = ['recipe', 'tag']
        ordering = ['tag']
        verbose_name = 'Recipe Tag'
        verbose_name_plural = 'Recipe Tags'

    def __str__(self):
        return f"{self.recipe.name} - {self.tag.name}"
