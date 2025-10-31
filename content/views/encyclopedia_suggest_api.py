from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import TrigramSimilarity
from content.models import Encyclopedia


@method_decorator(login_required, name='dispatch')
class EncyclopediaSuggestApiView(View):
    """
    API endpoint for fetching suggested encyclopedia entries based on fuzzy
    matching with a dish name. Requires authentication and staff permissions.
    """

    def get(self, request, *args, **kwargs):
        """
        Get suggested encyclopedia entries based on fuzzy matching.
        Query params: dish_name (required)
        """
        # Check if user is staff
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff permission required'}, status=403)

        dish_name = request.GET.get('dish_name', '').strip()

        if not dish_name:
            return JsonResponse({'suggestions': []})

        # Use PostgreSQL's trigram similarity for fuzzy matching
        # Filter by similarity threshold (0.25 catches more typos/variations)
        # Order by similarity score (highest first)
        suggestions = (
            Encyclopedia.objects
            .annotate(similarity=TrigramSimilarity('name', dish_name))
            .filter(similarity__gt=0.25)
            .order_by('-similarity')[:5]
        )

        # Format the results
        results = [
            {
                'id': entry.id,
                'name': entry.name,
                'slug': entry.slug,
                'description': entry.description[:100] if entry.description else '',
                'hierarchy': entry.get_hierarchy_breadcrumb(),
                'similarity': round(entry.similarity, 2)
            }
            for entry in suggestions
        ]

        return JsonResponse({'suggestions': results})
