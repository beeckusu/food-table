from django.views.generic import ListView
from content.models import Encyclopedia


class EncyclopediaListView(ListView):
    """
    List view for encyclopedia entries.
    Shows all encyclopedia entries (including hierarchical children) with pagination.
    Optimized with select_related/prefetch_related to prevent N+1 queries.
    """
    model = Encyclopedia
    template_name = 'encyclopedia/list.html'
    context_object_name = 'entries'
    paginate_by = 50

    def get_queryset(self):
        """Return all encyclopedia entries with optimized parent/child queries, ordered by name."""
        return Encyclopedia.objects.select_related('parent').prefetch_related('children').order_by('name')
