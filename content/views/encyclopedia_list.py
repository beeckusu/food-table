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
        # Recursively prefetch all descendants (up to reasonable depth)
        # We need to prefetch each level separately for the tree to work in templates
        return (
            Encyclopedia.objects
            .filter(parent__isnull=True)  # Only root entries
            .select_related('parent')
            .prefetch_related(
                'children',
                'children__children',
                'children__children__children',
                'children__children__children__children',
                'children__children__children__children__children',
            )
            .annotate(children_count=Count('children'))
            .order_by('name')
        )

    def get_context_data(self, **kwargs):
        """Add additional context for tree view."""
        context = super().get_context_data(**kwargs)

        # Recursively annotate all entries (including children) with computed properties
        def annotate_entry(entry):
            entry.depth = entry.get_depth()
            entry.has_children = entry.children.exists()
            # Recursively annotate children
            for child in entry.children.all():
                annotate_entry(child)

        # Annotate root entries and all their descendants
        for entry in context['entries']:
            annotate_entry(entry)

        # Add statistics
        context['total_entries'] = Encyclopedia.objects.count()

        # Calculate max depth
        max_depth = 0
        for entry in Encyclopedia.objects.all():
            depth = entry.get_depth()
            if depth > max_depth:
                max_depth = depth
        context['max_depth'] = max_depth + 1  # +1 because depth is 0-indexed

        return context
