from django.views.generic import ListView
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F
from content.models import Encyclopedia


class EncyclopediaSearchView(ListView):
    """
    Search view for encyclopedia entries.
    Searches name and description fields with relevance ranking.
    """
    model = Encyclopedia
    template_name = 'encyclopedia/search.html'
    context_object_name = 'entries'
    paginate_by = 50

    def get_queryset(self):
        """
        Filter entries by search query using full-text search.
        Returns results ranked by relevance.
        """
        query = self.request.GET.get('q', '').strip()

        if not query:
            # Return empty queryset for empty searches
            return Encyclopedia.objects.none()

        # Create search query
        search_query = SearchQuery(query)

        # Search using the search_vector field and rank results
        queryset = Encyclopedia.objects.annotate(
            rank=SearchRank(F('search_vector'), search_query)
        ).filter(
            search_vector=search_query
        ).order_by('-rank')

        return queryset

    def get_context_data(self, **kwargs):
        """Add search query to context."""
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context
