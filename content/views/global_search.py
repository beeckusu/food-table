from django.views.generic import ListView
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Value, CharField, Q
from itertools import chain
from operator import attrgetter
from content.models import Encyclopedia, Recipe, Review


class GlobalSearchView(ListView):
    """
    Global search view that searches across Encyclopedia, Recipe, and Review models.
    Supports query parameter (?q=...) and type filter (?type=encyclopedia|recipe|review).
    Results are ranked by relevance and can be filtered by content type.
    """
    template_name = 'search/results.html'
    context_object_name = 'results'
    paginate_by = 50

    def get_queryset(self):
        """
        Search across all content types and combine results.
        Returns results ranked by relevance, optionally filtered by type.
        """
        query = self.request.GET.get('q', '').strip()
        content_type = self.request.GET.get('type', '').strip().lower()

        if not query:
            # Return empty list for empty searches
            return []

        # Create search query
        search_query = SearchQuery(query)

        results = []

        # Search Encyclopedia (if not filtered or filtered to encyclopedia)
        if not content_type or content_type == 'encyclopedia':
            encyclopedia_results = Encyclopedia.objects.annotate(
                rank=SearchRank(F('search_vector'), search_query),
                content_type=Value('encyclopedia', output_field=CharField())
            ).filter(
                search_vector=search_query
            ).order_by('-rank')
            results.extend(list(encyclopedia_results))

        # Search Recipe (if not filtered or filtered to recipe)
        if not content_type or content_type == 'recipe':
            recipe_results = Recipe.objects.filter(
                is_private=False
            ).annotate(
                rank=SearchRank(F('search_vector'), search_query),
                content_type=Value('recipe', output_field=CharField())
            ).filter(
                search_vector=search_query
            ).order_by('-rank')
            results.extend(list(recipe_results))

        # Search Review (if not filtered or filtered to review)
        if not content_type or content_type == 'review':
            review_results = Review.objects.filter(
                is_private=False
            ).annotate(
                rank=SearchRank(F('search_vector'), search_query),
                content_type=Value('review', output_field=CharField())
            ).filter(
                search_vector=search_query
            ).order_by('-rank')
            results.extend(list(review_results))

        # Sort combined results by rank (descending)
        results.sort(key=attrgetter('rank'), reverse=True)

        return results

    def get_context_data(self, **kwargs):
        """Add search query and type filter to context."""
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['filter_type'] = self.request.GET.get('type', '')

        # Count results by type
        if context['results']:
            context['encyclopedia_count'] = sum(1 for r in context['results'] if r.content_type == 'encyclopedia')
            context['recipe_count'] = sum(1 for r in context['results'] if r.content_type == 'recipe')
            context['review_count'] = sum(1 for r in context['results'] if r.content_type == 'review')
        else:
            context['encyclopedia_count'] = 0
            context['recipe_count'] = 0
            context['review_count'] = 0

        return context
