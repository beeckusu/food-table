from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from content.models import Restaurant


class RestaurantUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()

        restaurant = get_object_or_404(Restaurant, pk=pk)

        name = request.POST.get('name', '').strip()
        street_address = request.POST.get('street_address', '').strip()
        city = request.POST.get('city', '').strip()
        province = request.POST.get('province', '').strip()
        country = request.POST.get('country', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()

        if not name:
            return redirect('content:restaurant_list')

        # Merge if same name and addresses are compatible:
        # - exact address match, OR
        # - one side has no address (same place, just entered without detail)
        # Skips merge when both sides have non-empty but different addresses (chains).
        same_name = Restaurant.objects.filter(name=name).exclude(pk=pk)
        if street_address:
            target = same_name.filter(
                Q(street_address=street_address) | Q(street_address='')
            ).first()
        else:
            target = same_name.filter(street_address='').first()

        if target:
            # Merge: re-point all related objects from this restaurant onto target
            restaurant.reviews.all().update(restaurant=target)
            restaurant.dishes.all().update(restaurant=target)
            if restaurant.visited and not target.visited:
                Restaurant.objects.filter(pk=target.pk).update(visited=True)
            restaurant.delete()
        else:
            restaurant.name = name
            restaurant.street_address = street_address
            restaurant.city = city
            restaurant.province = province
            restaurant.country = country
            restaurant.postal_code = postal_code
            restaurant.save()

        return redirect('content:restaurant_list')
