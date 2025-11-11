from django.http import JsonResponse
from django.views import View
from django.db.models import Q, Count
from content.models import Review


class RestaurantSearchApiView(View):
    """
    API endpoint for searching restaurant names.
    Returns JSON with autocomplete suggestions based on existing reviews.
    Supports partial matching for better user experience.
    """

    def get(self, request, *args, **kwargs):
        """
        Search restaurant names and return JSON response.
        Query parameter: q (search query)

        Returns unique restaurant names with their frequency and location info.
        """
        query = request.GET.get('q', '').strip()

        if not query or len(query) < 2:
            return JsonResponse({'results': []})

        # Search for restaurants with case-insensitive partial matching
        # Group by restaurant_name to get unique names with additional info
        restaurants = Review.objects.filter(
            restaurant_name__icontains=query
        ).values(
            'restaurant_name', 'location'
        ).annotate(
            visit_count=Count('id')
        ).order_by('-visit_count', 'restaurant_name')[:20]

        # Build results with restaurant info
        results = []
        seen_names = set()

        for restaurant in restaurants:
            name = restaurant['restaurant_name']
            # Only include unique restaurant names
            if name not in seen_names:
                seen_names.add(name)
                results.append({
                    'name': name,
                    'location': restaurant['location'] or '',
                    'visit_count': restaurant['visit_count']
                })

        return JsonResponse({'results': results})
