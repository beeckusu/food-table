from django.views.generic import DetailView
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from content.models import Restaurant, RestaurantDish
from content.forms import RestaurantDishForm


class RestaurantDetailView(LoginRequiredMixin, DetailView):
    model = Restaurant
    template_name = 'restaurant/detail.html'
    context_object_name = 'restaurant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant = self.object
        context['dishes_had'] = restaurant.dishes.filter(
            status=RestaurantDish.STATUS_HAD
        ).select_related('review')
        context['dishes_wishlist'] = restaurant.dishes.filter(
            status=RestaurantDish.STATUS_WISHLIST
        )
        context['had_form'] = RestaurantDishForm(initial={'status': RestaurantDish.STATUS_HAD})
        context['wishlist_form'] = RestaurantDishForm(initial={'status': RestaurantDish.STATUS_WISHLIST})
        context['reviews'] = restaurant.reviews.filter(is_private=False).prefetch_related(
            'review_dishes'
        ).order_by('-visit_date')
        return context


class RestaurantToggleVisitedView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        restaurant = get_object_or_404(Restaurant, pk=pk)
        restaurant.visited = not restaurant.visited
        restaurant.save(update_fields=['visited'])
        return redirect('content:restaurant_detail', pk=pk)


class RestaurantDishCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        restaurant = get_object_or_404(Restaurant, pk=pk)
        form = RestaurantDishForm(request.POST)
        if form.is_valid():
            dish = form.save(commit=False)
            dish.restaurant = restaurant
            dish.save()
        return redirect('content:restaurant_detail', pk=pk)


class RestaurantDishUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, dish_pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        restaurant = get_object_or_404(Restaurant, pk=pk)
        dish = get_object_or_404(RestaurantDish, pk=dish_pk, restaurant=restaurant)
        form = RestaurantDishForm(request.POST, instance=dish)
        if form.is_valid():
            form.save()
        return redirect('content:restaurant_detail', pk=pk)


class RestaurantDishDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, dish_pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        restaurant = get_object_or_404(Restaurant, pk=pk)
        dish = get_object_or_404(RestaurantDish, pk=dish_pk, restaurant=restaurant)
        dish.delete()
        return redirect('content:restaurant_detail', pk=pk)


class RestaurantDishMarkTriedView(LoginRequiredMixin, View):
    def post(self, request, pk, dish_pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        restaurant = get_object_or_404(Restaurant, pk=pk)
        dish = get_object_or_404(RestaurantDish, pk=dish_pk, restaurant=restaurant)
        dish.status = RestaurantDish.STATUS_HAD
        review_id = request.POST.get('review_id')
        if review_id:
            from content.models import Review
            try:
                dish.review = Review.objects.get(pk=review_id, restaurant=restaurant)
            except Review.DoesNotExist:
                pass
        dish.save()
        return redirect('content:restaurant_detail', pk=pk)
