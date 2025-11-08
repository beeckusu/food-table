from django.views.generic import DetailView
from content.models import Encyclopedia


class EncyclopediaDetailView(DetailView):
    """
    Detail view for a single encyclopedia entry.
    Displays full entry details including hierarchy, images, and tags.
    """
    model = Encyclopedia
    template_name = 'encyclopedia/detail.html'
    context_object_name = 'entry'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        """Add additional context for ancestors, children, and related content."""
        context = super().get_context_data(**kwargs)
        entry = self.object

        # Add breadcrumb navigation
        context['ancestors'] = entry.get_ancestors()

        # Add child entries
        context['children'] = entry.children.all().order_by('name')

        # Add images
        context['images'] = entry.images.all()

        # Add tags
        context['tags'] = entry.encyclopedia_tags.all()

        # Add related recipes with optimized query
        context['related_recipes'] = entry.recipes.prefetch_related('images').all()

        # Add tree entries for sidebar navigation with full tree structure
        root_entries = (
            Encyclopedia.objects
            .filter(parent__isnull=True)
            .prefetch_related('children')
            .order_by('name')
        )

        # Recursively annotate all entries with computed properties
        def annotate_entry(entry_obj):
            entry_obj.depth = entry_obj.get_depth()
            entry_obj.has_children = entry_obj.children.exists()
            # Recursively annotate children
            for child in entry_obj.children.all():
                annotate_entry(child)

        # Annotate root entries and all their descendants
        for root_entry in root_entries:
            annotate_entry(root_entry)

        context['entries'] = root_entries

        return context
