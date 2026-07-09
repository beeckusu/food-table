from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from content.models import FoodFestival


class FoodFestivalSearchApiView(LoginRequiredMixin, View):
    """
    API endpoint for searching food festival names.
    Returns JSON with autocomplete suggestions based on existing FoodFestival records.
    """

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()

        if not query or len(query) < 2:
            return JsonResponse({'results': []})

        festivals = FoodFestival.objects.filter(
            name__icontains=query
        ).order_by('name')[:20]

        results = [
            {
                'id': f.pk,
                'name': f.name,
                'city': f.city,
                'country': f.country,
                'review_count': f.reviews.count(),
            }
            for f in festivals
        ]

        return JsonResponse({'results': results})
