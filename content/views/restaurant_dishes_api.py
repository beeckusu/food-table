from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from content.models import Restaurant


class RestaurantDishesApiView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()

        restaurant = get_object_or_404(Restaurant, pk=pk)
        source_detail = (request.GET.get('source_detail') or '').strip()

        dishes = restaurant.dishes.order_by('status', 'dish_name')
        results = []
        for dish in dishes:
            recommended = bool(source_detail) and dish.references.filter(source_detail=source_detail).exists()
            results.append({
                'id': dish.pk,
                'name': dish.dish_name,
                'status': dish.status,
                'notes': dish.notes,
                'recommended': recommended,
            })

        return JsonResponse({'results': results})
