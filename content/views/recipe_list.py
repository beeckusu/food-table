from django.views.generic import ListView
from content.models import Recipe


class RecipeListView(ListView):
    """
    List view for recipes.
    Shows all public recipes ordered by name with pagination.
    """
    model = Recipe
    template_name = 'recipe/list.html'
    context_object_name = 'recipes'
    paginate_by = 50

    def get_queryset(self):
        """
        Return all public recipes ordered by name.
        Optimizes queries with select_related and prefetch_related.
        """
        return Recipe.objects.filter(
            is_private=False
        ).select_related(
            'created_by',
            'encyclopedia_entry'
        ).prefetch_related(
            'images',
            'recipe_tags'
        ).order_by('name')
