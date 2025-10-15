from django.views.generic import TemplateView
from content.models import Review, Encyclopedia, Recipe


class HomeView(TemplateView):
    """
    Home page view displaying recent reviews, quick links, and stats.
    """
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        """
        Add recent reviews and stats to the context.
        """
        context = super().get_context_data(**kwargs)

        # Get 10 most recent public reviews
        context['recent_reviews'] = Review.objects.filter(
            is_private=False
        ).select_related(
            'created_by'
        ).prefetch_related(
            'images',
            'review_dishes'
        ).order_by('-visit_date', '-entry_time')[:10]

        # Calculate stats
        context['stats'] = {
            'encyclopedia_count': Encyclopedia.objects.count(),
            'review_count': Review.objects.filter(is_private=False).count(),
            'recipe_count': Recipe.objects.count(),
        }

        return context
