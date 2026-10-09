from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from content.models import RestaurantDish
from content.views.dish_link_api import is_staff_user
import json


@method_decorator([login_required, user_passes_test(is_staff_user)], name='dispatch')
class RestaurantDishExcitementApiView(View):
    """
    API endpoint for rating how excited you are to try a RestaurantDish.
    POST body: {"excitement": 1-10} to set, or {"excitement": null} to clear.
    """

    def post(self, request, dish_id, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if 'excitement' not in data:
            return JsonResponse({'error': 'excitement is required'}, status=400)

        excitement = data['excitement']
        if not RestaurantDish.is_valid_excitement(excitement):
            return JsonResponse({
                'error': f'excitement must be an integer from {RestaurantDish.EXCITEMENT_MIN} '
                         f'to {RestaurantDish.EXCITEMENT_MAX}, or null'
            }, status=400)

        dish = get_object_or_404(RestaurantDish, id=dish_id)
        dish.excitement = excitement
        dish.save(update_fields=['excitement'])

        return JsonResponse({
            'success': True,
            'dish': {'id': dish.id, 'excitement': dish.excitement},
        })
