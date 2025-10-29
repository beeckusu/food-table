from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from content.models import ReviewDish, Encyclopedia
import json


@method_decorator(login_required, name='dispatch')
class DishLinkApiView(View):
    """
    API endpoint for linking a ReviewDish to an Encyclopedia entry.
    Requires authentication.
    """

    def post(self, request, dish_id, *args, **kwargs):
        """
        Link a dish to an encyclopedia entry.
        POST body: {"encyclopedia_id": <id>}
        """
        try:
            # Parse request body
            data = json.loads(request.body)
            encyclopedia_id = data.get('encyclopedia_id')

            if not encyclopedia_id:
                return JsonResponse({'error': 'encyclopedia_id is required'}, status=400)

            # Get the dish and encyclopedia entry
            dish = get_object_or_404(ReviewDish, id=dish_id)
            encyclopedia_entry = get_object_or_404(Encyclopedia, id=encyclopedia_id)

            # Update the link
            dish.encyclopedia_entry = encyclopedia_entry
            dish.save()

            # Return updated dish info
            return JsonResponse({
                'success': True,
                'dish': {
                    'id': dish.id,
                    'encyclopedia_entry': {
                        'id': encyclopedia_entry.id,
                        'name': encyclopedia_entry.name,
                        'slug': encyclopedia_entry.slug,
                        'hierarchy': encyclopedia_entry.get_hierarchy_breadcrumb(),
                    }
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def delete(self, request, dish_id, *args, **kwargs):
        """
        Unlink a dish from its encyclopedia entry.
        """
        try:
            dish = get_object_or_404(ReviewDish, id=dish_id)
            dish.encyclopedia_entry = None
            dish.save()

            return JsonResponse({
                'success': True,
                'dish': {
                    'id': dish.id,
                    'encyclopedia_entry': None
                }
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
