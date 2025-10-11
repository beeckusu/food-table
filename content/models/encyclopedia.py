from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver


class Encyclopedia(models.Model):
    """
    Encyclopedia model for storing food-related knowledge entries with hierarchical structure.
    """
    # Core Identity Fields
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField()

    # Hierarchical Structure
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )

    # Classification Fields
    cuisine_type = models.CharField(max_length=100, blank=True, null=True)
    dish_category = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)

    # Content Fields
    cultural_significance = models.TextField(blank=True)
    popular_examples = models.TextField(blank=True)
    history = models.TextField(blank=True)
    similar_dishes = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='similar_to'
    )

    # Metadata Fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='encyclopedia_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    search_vector = SearchVectorField(null=True, blank=True)

    # GenericRelation for images (from FT-7)
    images = GenericRelation('Image')

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Encyclopedia Entries'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
            models.Index(fields=['cuisine_type']),
            models.Index(fields=['dish_category']),
        ]

    def __str__(self):
        return self.name

    def get_ancestors(self):
        """
        Get all ancestors of this entry, starting from the immediate parent
        and going up to the root.
        """
        ancestors = []
        current = self.parent
        visited = set()  # Prevent infinite loops

        while current is not None:
            if current.id in visited:
                break
            visited.add(current.id)
            ancestors.append(current)
            current = current.parent

        return ancestors

    def get_descendants(self):
        """
        Get all descendants of this entry recursively.
        """
        descendants = []
        visited = set()  # Prevent infinite loops

        def collect_children(entry):
            if entry.id in visited:
                return
            visited.add(entry.id)

            for child in entry.children.all():
                descendants.append(child)
                collect_children(child)

        collect_children(self)
        return descendants

    def _check_cycle(self):
        """
        Check if setting the parent would create a cycle in the hierarchy.
        """
        if self.parent is None:
            return

        # Can't be parent of itself
        if self.parent.id == self.id:
            raise ValidationError("An entry cannot be its own parent.")

        # Check if parent is in descendants
        current = self.parent
        visited = set()

        while current is not None:
            if current.id == self.id:
                raise ValidationError(
                    f"Setting '{self.parent.name}' as parent would create a cycle. "
                    f"'{self.name}' is an ancestor of '{self.parent.name}'."
                )
            if current.id in visited:
                break
            visited.add(current.id)
            current = current.parent

    def save(self, *args, **kwargs):
        """
        Override save to perform cycle prevention check.
        """
        if self.parent is not None:
            self._check_cycle()
        super().save(*args, **kwargs)


@receiver(post_save, sender=Encyclopedia)
def update_search_vector(sender, instance, **kwargs):
    """
    Signal handler to automatically update search_vector field when Encyclopedia is saved.
    Updates the search vector with combined name and description content.
    """
    # Avoid infinite recursion by checking if we're already updating
    if kwargs.get('update_fields') and 'search_vector' in kwargs['update_fields']:
        return

    # Update search_vector with name and description
    Encyclopedia.objects.filter(pk=instance.pk).update(
        search_vector=SearchVector('name', weight='A') + SearchVector('description', weight='B')
    )
