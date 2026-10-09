from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from content.models import RestaurantDish, Encyclopedia
from content.views.dish_link_api import is_staff_user
import json


@method_decorator([login_required, user_passes_test(is_staff_user)], name='dispatch')
class RestaurantDishLinkApiView(View):
    """
    API endpoint for classifying a RestaurantDish (e.g. an anticipated/wishlist
    dish) by linking it to an Encyclopedia entry. Mirrors DishLinkApiView's
    request/response shape so the same badge JS can drive both.
    """

    def post(self, request, dish_id, *args, **kwargs):
        """
        Link a restaurant dish to an encyclopedia entry.
        POST body: {"encyclopedia_id": <id>}
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        encyclopedia_id = data.get('encyclopedia_id')
        if not encyclopedia_id:
            return JsonResponse({'error': 'encyclopedia_id is required'}, status=400)

        dish = get_object_or_404(RestaurantDish, id=dish_id)
        encyclopedia_entry = get_object_or_404(Encyclopedia, id=encyclopedia_id)

        dish.encyclopedia_entry = encyclopedia_entry
        dish.save(update_fields=['encyclopedia_entry'])

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

    def delete(self, request, dish_id, *args, **kwargs):
        """
        Unlink a restaurant dish from its encyclopedia entry.
        """
        dish = get_object_or_404(RestaurantDish, id=dish_id)
        dish.encyclopedia_entry = None
        dish.save(update_fields=['encyclopedia_entry'])

        return JsonResponse({
            'success': True,
            'dish': {
                'id': dish.id,
                'encyclopedia_entry': None
            }
        })
