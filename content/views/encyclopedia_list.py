from django.views.generic import ListView
from content.models import Encyclopedia
from content.utils.encyclopedia import build_encyclopedia_tree


class EncyclopediaListView(ListView):
    """
    Tree view for encyclopedia entries.
    Shows root-level encyclopedia entries with hierarchical structure.
    Child entries are accessible via the tree expansion UI.
    """
    model = Encyclopedia
    template_name = 'encyclopedia/list.html'
    context_object_name = 'entries'
    paginate_by = None

    def get_queryset(self):
        # Overridden by get_context_data; return empty to satisfy ListView contract
        return Encyclopedia.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        roots, max_depth = build_encyclopedia_tree()
        context['entries'] = roots
        context['total_entries'] = Encyclopedia.objects.filter(is_placeholder=False).count()
        context['max_depth'] = max_depth + 1  # +1 because depth is 0-indexed

        return context
