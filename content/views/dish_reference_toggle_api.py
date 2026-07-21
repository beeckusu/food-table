import json
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from content.models import RestaurantDish, RestaurantDishReference


class DishReferenceToggleApiView(LoginRequiredMixin, View):
    def post(self, request, dish_id):
        if not request.user.is_staff:
            return HttpResponseForbidden()

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        source = (data.get('source') or '').strip()
        source_detail = (data.get('source_detail') or '').strip()
        if not source_detail:
            return JsonResponse({'error': 'source_detail is required'}, status=400)

        dish = get_object_or_404(RestaurantDish, pk=dish_id)
        existing = dish.references.filter(source=source, source_detail=source_detail).first()
        if existing:
            existing.delete()
            recommended = False
        else:
            RestaurantDishReference.objects.create(dish=dish, source=source, source_detail=source_detail)
            recommended = True

        return JsonResponse({'success': True, 'recommended': recommended})
