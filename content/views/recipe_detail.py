from django.views.generic import DetailView
from content.models import Recipe


class RecipeDetailView(DetailView):
    """
    Detail view for a single recipe.
    Displays full recipe details including ingredients, steps, images, tags, and related recipes.
    """
    model = Recipe
    template_name = 'recipe/detail.html'
    context_object_name = 'recipe'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """Only show public recipes."""
        return Recipe.objects.filter(is_private=False)

    def get_context_data(self, **kwargs):
        """Add additional context for images, tags, and related recipes."""
        context = super().get_context_data(**kwargs)
        recipe = self.object

        # Add images
        context['images'] = recipe.images.all()

        # Add tags
        context['tags'] = recipe.recipe_tags.select_related('tag').all()

        # Add related recipes (recipes linked to the same encyclopedia entry, excluding current)
        if recipe.encyclopedia_entry:
            context['related_recipes'] = Recipe.objects.filter(
                encyclopedia_entry=recipe.encyclopedia_entry,
                is_private=False
            ).exclude(
                id=recipe.id
            ).prefetch_related(
                'images'
            ).order_by('name')[:5]
        else:
            context['related_recipes'] = []

        return context
