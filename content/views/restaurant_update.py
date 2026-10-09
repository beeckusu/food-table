from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from content.models import MenuItem, Restaurant


def _merge_menu_items(source, target):
    """
    Move source's MenuItems onto target. Where target already has an item with
    the same name_key (unique per restaurant), fold the source item's review
    dishes into it and drop the duplicate instead of violating the constraint.
    """
    target_items = {item.name_key: item for item in target.menu_items.all()}
    for item in source.menu_items.all():
        existing = target_items.get(item.name_key)
        if existing is None:
            MenuItem.objects.filter(pk=item.pk).update(restaurant=target)
            continue
        item.review_dishes.all().update(menu_item=existing)
        if existing.encyclopedia_entry_id is None and item.encyclopedia_entry_id:
            existing.encyclopedia_entry_id = item.encyclopedia_entry_id
            existing.save(update_fields=['encyclopedia_entry'])
        item.delete()


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
        is_pop_up = request.POST.get('is_pop_up') == 'on'
        website = request.POST.get('website', '').strip()

        if not name:
            return redirect('content:restaurant_list')
        if is_pop_up and not website:
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
            with transaction.atomic():
                restaurant.reviews.all().update(restaurant=target)
                restaurant.dishes.all().update(restaurant=target)
                _merge_menu_items(restaurant, target)
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
            restaurant.is_pop_up = is_pop_up
            restaurant.website = website
            restaurant.save()

        return redirect('content:restaurant_list')
