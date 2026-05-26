from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import HttpResponseForbidden
from django.forms import formset_factory
from content.models import RestaurantDish, ApiUsageLog
from content.forms import RestaurantForm, RestaurantDishInlineForm


HadDishFormSet = formset_factory(RestaurantDishInlineForm, extra=1, can_delete=True)
WishlistDishFormSet = formset_factory(RestaurantDishInlineForm, extra=1, can_delete=True)


class RestaurantCreateView(LoginRequiredMixin, View):
    template_name = 'restaurant/create.html'

    def _get_context(self, restaurant_form=None, had_formset=None, wishlist_formset=None):
        return {
            'restaurant_form': restaurant_form or RestaurantForm(),
            'had_formset': had_formset or HadDishFormSet(prefix='had'),
            'wishlist_formset': wishlist_formset or WishlistDishFormSet(prefix='wishlist'),
            'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        }

    def get(self, request):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return render(request, self.template_name, self._get_context())

    def post(self, request):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        restaurant_form = RestaurantForm(request.POST)
        had_formset = HadDishFormSet(request.POST, prefix='had')
        wishlist_formset = WishlistDishFormSet(request.POST, prefix='wishlist')

        if restaurant_form.is_valid() and had_formset.is_valid() and wishlist_formset.is_valid():
            restaurant = restaurant_form.save(commit=False)
            restaurant.created_by = request.user
            restaurant.save()

            if request.POST.get('places_session_used') == '1':
                ApiUsageLog.objects.create(endpoint='places')

            for form in had_formset:
                if form.cleaned_data.get('dish_name'):
                    dish = form.save(commit=False)
                    dish.restaurant = restaurant
                    dish.status = RestaurantDish.STATUS_HAD
                    dish.save()

            for form in wishlist_formset:
                if form.cleaned_data.get('dish_name'):
                    dish = form.save(commit=False)
                    dish.restaurant = restaurant
                    dish.status = RestaurantDish.STATUS_WISHLIST
                    dish.save()

            return redirect('content:restaurant_detail', pk=restaurant.pk)

        return render(request, self.template_name, self._get_context(
            restaurant_form=restaurant_form,
            had_formset=had_formset,
            wishlist_formset=wishlist_formset,
        ))
