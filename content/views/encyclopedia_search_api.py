from django.db.utils import ProgrammingError
from django.http import JsonResponse
from django.views import View
from django.contrib.postgres.search import SearchRank
from django.db.models import F, Q
from content.models import Encyclopedia
from content.utils.search import build_prefix_search_query


class EncyclopediaSearchApiView(View):
    """
    API endpoint for searching encyclopedia entries.
    Returns JSON with search results including hierarchy breadcrumbs.
    Supports partial matching for better user experience.
    """

    def get(self, request, *args, **kwargs):
        """
        Search encyclopedia entries and return JSON response.
        Query parameter: q (search query)

        Uses a multi-strategy approach:
        1. Full-text search with prefix matching (e.g., "chee:*" matches "cheese")
        2. Fallback to case-insensitive ILIKE for partial matches
        """
        query = request.GET.get('q', '').strip()

        if not query:
            return JsonResponse({'results': []})

        # Strategy 1: Try full-text search with prefix matching.
        search_query = build_prefix_search_query(query)
        if search_query is not None:
            try:
                entries = Encyclopedia.objects.annotate(
                    rank=SearchRank(F('search_vector'), search_query)
                ).filter(
                    search_vector=search_query
                ).select_related('parent')
                has_results = entries.exists()
            except ProgrammingError:
                has_results = False
        else:
            has_results = False

        # Strategy 2: If no results, fallback to ILIKE partial matching
        if not has_results:
            entries = Encyclopedia.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            ).select_related('parent')

        # Limit to top 20 results and order by relevance
        entries = entries[:20]

        # Build results with hierarchy
        results = []
        for entry in entries:
            results.append({
                'id': entry.id,
                'name': entry.name,
                'slug': entry.slug,
                'hierarchy': entry.get_hierarchy_breadcrumb(),
                'cuisine_type': entry.cuisine_type or '',
                'dish_category': entry.dish_category or '',
            })

        return JsonResponse({'results': results})
