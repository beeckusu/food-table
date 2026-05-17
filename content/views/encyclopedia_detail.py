from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from content.models import Encyclopedia
from content.utils.encyclopedia import build_encyclopedia_tree


class EncyclopediaDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a single encyclopedia entry.
    Displays full entry details including hierarchy, images, and tags.
    """
    model = Encyclopedia
    template_name = 'encyclopedia/detail.html'
    context_object_name = 'entry'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """
        Optimize queryset with prefetch_related for better performance.
        Note: We don't prefetch similar_dishes here because it's a symmetrical ManyToMany
        relationship, which would cause infinite recursion during prefetch.
        """
        return Encyclopedia.objects.all()

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

        # Add related review dishes with optimized query to avoid N+1 queries
        context['related_review_dishes'] = (
            entry.dish_reviews
            .select_related('review')
            .prefetch_related('images', 'review__images')
            .order_by('-review__visit_date', '-review__entry_time')
        )

        # Add similar dishes with optimized query
        # Convert to list to prevent recursion issues with symmetrical ManyToMany relationship
        context['similar_dishes'] = list(entry.similar_dishes.all().order_by('name'))

        roots, _ = build_encyclopedia_tree()
        context['entries'] = roots

        return context
