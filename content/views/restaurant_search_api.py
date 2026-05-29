from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from content.models import Restaurant


class RestaurantSearchApiView(LoginRequiredMixin, View):
    """
    API endpoint for searching restaurant names.
    Returns JSON with autocomplete suggestions based on existing Restaurant records.
    Supports partial matching for better user experience.
    """

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()

        if not query or len(query) < 2:
            return JsonResponse({'results': []})

        restaurants = Restaurant.objects.filter(
            name__icontains=query
        ).order_by('name')[:20]

        results = [
            {
                'id': r.pk,
                'name': r.name,
                'street_address': r.street_address,
                'city': r.city,
                'province': r.province,
                'country': r.country,
                'postal_code': r.postal_code,
                'visit_count': r.reviews.count(),
            }
            for r in restaurants
        ]

        return JsonResponse({'results': results})
