from django.views.generic import ListView
from content.models import Encyclopedia


class EncyclopediaListView(ListView):
    """
    List view for encyclopedia entries.
    Shows all top-level entries (parent=None) with pagination.
    """
    model = Encyclopedia
    template_name = 'encyclopedia/list.html'
    context_object_name = 'entries'
    paginate_by = 50

    def get_queryset(self):
        """Filter to show only top-level entries ordered by name."""
        return Encyclopedia.objects.filter(parent=None).order_by('name')
