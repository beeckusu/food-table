import json
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from content.models import Restaurant, RestaurantDish, ApiUsageLog


class WishlistBulkCreateApiView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_staff:
            return HttpResponseForbidden()

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        url = (data.get('url') or '').strip()
        restaurant_id = data.get('restaurant_id')
        restaurant_name = (data.get('restaurant_name') or '').strip()
        dish_names = [d.strip() for d in data.get('dishes', []) if d and d.strip()]

        if restaurant_id:
            restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        elif restaurant_name:
            restaurant = Restaurant.objects.filter(name=restaurant_name).first()
            if not restaurant:
                restaurant = Restaurant.objects.create(
                    name=restaurant_name,
                    street_address=(data.get('street_address') or '').strip(),
                    city=(data.get('city') or '').strip(),
                    province=(data.get('province') or '').strip(),
                    country=(data.get('country') or '').strip(),
                    postal_code=(data.get('postal_code') or '').strip(),
                    created_by=request.user,
                )
                if data.get('places_session_used'):
                    ApiUsageLog.objects.create(endpoint='places')
        else:
            return JsonResponse({'error': 'Restaurant name is required'}, status=400)

        source_detail = url[:255] if url else ''
        for dish_name in dish_names:
            RestaurantDish.objects.create(
                restaurant=restaurant,
                dish_name=dish_name,
                status=RestaurantDish.STATUS_WISHLIST,
                source='Instagram',
                source_detail=source_detail,
            )

        return JsonResponse({
            'success': True,
            'restaurant_id': restaurant.pk,
            'restaurant_name': restaurant.name,
        })
