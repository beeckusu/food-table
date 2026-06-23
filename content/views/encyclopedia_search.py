from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Case, When, Value, IntegerField
from content.models import Encyclopedia


class EncyclopediaSearchView(LoginRequiredMixin, ListView):
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

        # Exact matches on name/cuisine_type are boosted to the top, ahead of
        # SearchRank, since a description that mentions the query several
        # times can otherwise out-rank the entry the user is actually after.
        queryset = Encyclopedia.objects.annotate(
            rank=SearchRank(F('search_vector'), search_query),
            exact_name_match=Case(When(name__iexact=query, then=Value(1)), default=Value(0), output_field=IntegerField()),
            exact_cuisine_match=Case(When(cuisine_type__iexact=query, then=Value(1)), default=Value(0), output_field=IntegerField())
        ).filter(
            search_vector=search_query
        ).order_by('-exact_name_match', '-exact_cuisine_match', '-rank')

        return queryset

    def get_context_data(self, **kwargs):
        """Add search query to context."""
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context
