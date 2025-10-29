from django.views.generic import ListView
from django.db.models import Count
from content.models import Encyclopedia


class EncyclopediaListView(ListView):
    """
    Tree view for encyclopedia entries.
    Shows root-level encyclopedia entries with hierarchical structure.
    Child entries are accessible via the tree expansion UI.
    """
    model = Encyclopedia
    template_name = 'encyclopedia/list.html'
    context_object_name = 'entries'
    paginate_by = None  # No pagination for tree view - show all roots

    def get_queryset(self):
        """
        Return only root encyclopedia entries (no parent) with:
        - Optimized queries for children relationships
        - Annotated with children count
        - Ordered by name
        """
        return (
            Encyclopedia.objects
            .filter(parent__isnull=True)  # Only root entries
            .select_related('parent')
            .prefetch_related('children')
            .annotate(children_count=Count('children'))
            .order_by('name')
        )

    def get_context_data(self, **kwargs):
        """Add additional context for tree view."""
        context = super().get_context_data(**kwargs)

        # Annotate each entry with computed properties for template
        for entry in context['entries']:
            entry.depth = entry.get_depth()
            entry.has_children = entry.children.exists()

        return context
