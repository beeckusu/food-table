from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models.signals import post_save
from django.dispatch import receiver
from .encyclopedia import Encyclopedia


class Recipe(models.Model):
    """
    Recipe model for storing cooking recipes with structured ingredients and steps.
    """
    # Difficulty choices
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'
    DIFFICULTY_CHOICES = [
        (EASY, 'Easy'),
        (MEDIUM, 'Medium'),
        (HARD, 'Hard'),
    ]

    # Core Identity Fields
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField()

    # Recipe Details
    servings = models.PositiveIntegerField(null=True, blank=True)
    prep_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    cook_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    total_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default=MEDIUM
    )

    # Structured JSON Fields
    # Example ingredients structure: [{"item": "flour", "quantity": "2 cups", "notes": "all-purpose"}]
    ingredients = models.JSONField(default=list, blank=True)
    # Example steps structure: [{"order": 1, "instruction": "Mix ingredients", "time_minutes": 5}]
    steps = models.JSONField(default=list, blank=True)

    # Additional Content Fields
    tips = models.TextField(blank=True)
    dietary_restrictions = models.JSONField(default=list, blank=True)

    # Relationships
    encyclopedia_entry = models.ForeignKey(
        Encyclopedia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipes'
    )

    # Metadata Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recipes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1)
    is_private = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    search_vector = SearchVectorField(null=True, blank=True)

    # GenericRelation for images
    images = GenericRelation('Image')

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['encyclopedia_entry']),
            models.Index(fields=['is_private']),
        ]

    def __str__(self):
        return self.name


@receiver(post_save, sender=Recipe)
def update_recipe_search_vector(sender, instance, **kwargs):
    """
    Signal handler to automatically update search_vector field when Recipe is saved.
    Updates the search vector with combined name and description content.
    """
    # Avoid infinite recursion by checking if we're already updating
    if kwargs.get('update_fields') and 'search_vector' in kwargs['update_fields']:
        return

    # Update search_vector with name and description
    Recipe.objects.filter(pk=instance.pk).update(
        search_vector=SearchVector('name', weight='A') + SearchVector('description', weight='B')
    )
