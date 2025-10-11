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

        return context
