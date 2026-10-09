from django.views.generic import DetailView
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from content.models import FoodFestival, Restaurant, RestaurantDish, RestaurantDishReference
from content.forms import RestaurantDishForm
from content.views.restaurant_detail import carry_classification_to_menu_item


class FoodFestivalDetailView(LoginRequiredMixin, DetailView):
    model = FoodFestival
    template_name = 'food_festival/detail.html'
    context_object_name = 'food_festival'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        food_festival = self.object

        dishes_by_restaurant = {}
        all_dishes = food_festival.dishes.select_related('review').prefetch_related('references')
        for dish in all_dishes:
            dishes_by_restaurant.setdefault(dish.restaurant_id, []).append(dish)

        context['restaurant_groups'] = [
            {
                'restaurant': restaurant,
                'dishes_had': [d for d in dishes_by_restaurant.get(restaurant.id, []) if d.status == RestaurantDish.STATUS_HAD],
                'dishes_wishlist': [d for d in dishes_by_restaurant.get(restaurant.id, []) if d.status == RestaurantDish.STATUS_WISHLIST],
            }
            for restaurant in food_festival.restaurants.all()
        ]
        context['reviews'] = food_festival.reviews.filter(is_private=False).prefetch_related(
            'review_dishes'
        ).order_by('-visit_date')
        return context


def _resolve_restaurant_from_post(post_data, user):
    """Resolve a Restaurant from a restaurant_id select or a restaurant_name freetext fallback."""
    restaurant_id = post_data.get('restaurant_id')
    if restaurant_id:
        return get_object_or_404(Restaurant, pk=restaurant_id)
    name = post_data.get('restaurant_name', '').strip()
    if not name:
        return None
    restaurant, _ = Restaurant.objects.get_or_create(
        name=name,
        street_address='',
        defaults={'created_by': user},
    )
    return restaurant


class FoodFestivalAddRestaurantView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        food_festival = get_object_or_404(FoodFestival, pk=pk)

        restaurant = _resolve_restaurant_from_post(request.POST, request.user)
        if restaurant:
            food_festival.restaurants.add(restaurant)
        return redirect('content:food_festival_detail', pk=pk)


class FoodFestivalRemoveRestaurantView(LoginRequiredMixin, View):
    def post(self, request, pk, restaurant_pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        food_festival = get_object_or_404(FoodFestival, pk=pk)
        food_festival.restaurants.remove(restaurant_pk)
        return redirect('content:food_festival_detail', pk=pk)


class FoodFestivalDishCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        food_festival = get_object_or_404(FoodFestival, pk=pk)
        restaurant = _resolve_restaurant_from_post(request.POST, request.user)
        if not restaurant:
            return redirect('content:food_festival_detail', pk=pk)
        form = RestaurantDishForm(request.POST)
        if form.is_valid():
            dish = form.save(commit=False)
            dish.food_festival = food_festival
            dish.restaurant = restaurant
            dish.save()
            food_festival.restaurants.add(restaurant)
            _save_references(dish, request.POST)
        return redirect('content:food_festival_detail', pk=pk)


class FoodFestivalDishUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, dish_pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        food_festival = get_object_or_404(FoodFestival, pk=pk)
        dish = get_object_or_404(RestaurantDish, pk=dish_pk, food_festival=food_festival)
        form = RestaurantDishForm(request.POST, instance=dish)
        if form.is_valid():
            form.save()
            dish.references.all().delete()
            _save_references(dish, request.POST)
        return redirect('content:food_festival_detail', pk=pk)


class FoodFestivalDishDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, dish_pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        food_festival = get_object_or_404(FoodFestival, pk=pk)
        dish = get_object_or_404(RestaurantDish, pk=dish_pk, food_festival=food_festival)
        dish.delete()
        return redirect('content:food_festival_detail', pk=pk)


class FoodFestivalDishMarkTriedView(LoginRequiredMixin, View):
    def post(self, request, pk, dish_pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        food_festival = get_object_or_404(FoodFestival, pk=pk)
        dish = get_object_or_404(RestaurantDish, pk=dish_pk, food_festival=food_festival)
        dish.status = RestaurantDish.STATUS_HAD
        review_id = request.POST.get('review_id')
        if review_id:
            from content.models import Review
            try:
                dish.review = Review.objects.get(pk=review_id, food_festival=food_festival)
            except Review.DoesNotExist:
                pass
        dish.save()
        carry_classification_to_menu_item(dish)
        return redirect('content:food_festival_detail', pk=pk)


def _save_references(dish, post_data):
    sources = post_data.getlist('ref_source')
    details = post_data.getlist('ref_source_detail')
    for src, det in zip(sources, details):
        src, det = src.strip()[:255], det.strip()[:255]
        if src or det:
            RestaurantDishReference.objects.create(dish=dish, source=src, source_detail=det)
