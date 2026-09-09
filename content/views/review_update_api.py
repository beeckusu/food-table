import json
import logging

from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from content.models import Review, ReviewDish, RestaurantDish
from content.views.review_shared import (
    validate_review_data,
    resolve_restaurant,
    resolve_food_festival,
    resolve_dish_restaurant,
    sync_review_images,
    sync_dish_images,
    link_or_create_wishlist_dish,
    resolve_encyclopedia_entry,
    DishRestaurantResolutionError,
)

logger = logging.getLogger(__name__)


class ReviewEditDataApiView(LoginRequiredMixin, View):
    """Returns an existing review's data pre-shaped to match the review modal's formData structure."""

    def get(self, request, pk, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        try:
            review = Review.objects.select_related('restaurant', 'food_festival').prefetch_related(
                'review_dishes__encyclopedia_entry', 'review_dishes__images', 'images'
            ).get(pk=pk)
        except Review.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Review not found'}, status=404)

        restaurant = review.restaurant
        food_festival = review.food_festival

        dish_restaurants = {}
        if food_festival:
            for rd in RestaurantDish.objects.filter(review=review).select_related('restaurant'):
                dish_restaurants.setdefault(rd.dish_name, rd.restaurant)

        dishes = []
        for dish in review.review_dishes.all():
            dish_payload = {
                'id': dish.id,
                'name': dish.dish_name or (dish.encyclopedia_entry.name if dish.encyclopedia_entry else ''),
                'rating': dish.dish_rating if dish.dish_rating is not None else 50,
                'notes': dish.notes or '',
                'cost': str(dish.cost) if dish.cost is not None else None,
                'encyclopedia_ids': (
                    [{
                        'id': dish.encyclopedia_entry.id,
                        'name': dish.encyclopedia_entry.name,
                        'slug': dish.encyclopedia_entry.slug,
                    }] if dish.encyclopedia_entry else []
                ),
                'images': [{'id': img.id, 'src': img.image.url} for img in dish.images.all()],
            }
            if food_festival:
                dish_restaurant = dish_restaurants.get(dish.dish_name)
                dish_payload['restaurant'] = (
                    {'mode': 'search', 'id': dish_restaurant.id, 'name': dish_restaurant.name}
                    if dish_restaurant else {}
                )
            dishes.append(dish_payload)

        if restaurant:
            target_type = 'restaurant'
            restaurant_payload = {
                'mode': 'search',
                'id': restaurant.id,
                'name': restaurant.name,
                'isPopUp': restaurant.is_pop_up,
                'website': restaurant.website,
                'address': restaurant.street_address,
                'city': restaurant.city,
                'province': restaurant.province,
                'country': restaurant.country,
                'postalCode': restaurant.postal_code,
                'googlePlaceId': restaurant.google_place_id,
            }
            food_festival_payload = {}
        else:
            target_type = 'food_festival'
            restaurant_payload = {}
            food_festival_payload = {
                'mode': 'search',
                'id': food_festival.id,
                'name': food_festival.name,
                'city': food_festival.city,
                'country': food_festival.country,
                'startDate': food_festival.start_date.isoformat() if food_festival.start_date else '',
                'endDate': food_festival.end_date.isoformat() if food_festival.end_date else '',
                'website': food_festival.website,
            }

        data = {
            'targetType': target_type,
            'basicInfo': {
                'visitDate': review.visit_date.isoformat(),
                'partySize': review.party_size,
                'entryTime': review.entry_time.strftime('%H:%M') if review.entry_time else '',
            },
            'restaurant': restaurant_payload,
            'food_festival': food_festival_payload,
            'rating': {
                'overall': review.rating,
                'title': review.title or '',
                'notes': review.notes or '',
                'ambiance': review.metadata.get('ambiance_rating', 50),
                'service': review.metadata.get('service_rating', 50),
                'images': [{'id': img.id, 'src': img.image.url} for img in review.images.all()],
            },
            'dishes': dishes,
            'is_draft': review.is_draft,
        }
        return JsonResponse({'success': True, 'review': data})


class ReviewUpdateApiView(LoginRequiredMixin, View):
    """Updates an existing review with all related data (restaurant, dishes, images)."""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def patch(self, request, pk, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Review not found'}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)

        validation_errors = validate_review_data(data, dishes_required=True)
        if validation_errors:
            return JsonResponse({'success': False, 'errors': validation_errors}, status=400)

        target_type = data.get('targetType', 'restaurant')
        if target_type == 'food_festival':
            food_festival, target_error = resolve_food_festival(data.get('food_festival', {}), request.user)
            restaurant = None
            error_key = 'food_festival'
        else:
            restaurant, target_error = resolve_restaurant(data.get('restaurant', {}), request.user)
            food_festival = None
            error_key = 'restaurant'
        if target_error:
            return JsonResponse({'success': False, 'errors': {error_key: target_error}}, status=400)

        try:
            with transaction.atomic():
                self._update_review(review, data, restaurant, food_festival)

                image_errors = sync_review_images(review, data.get('rating', {}).get('images', []), request.user)
                image_errors.extend(self._sync_dishes(review, data.get('dishes', []), request.user))

            response = {
                'success': True,
                'review_id': review.id,
                'review_url': reverse('content:review_detail', kwargs={'pk': review.id}),
            }
            if image_errors:
                response['image_warnings'] = image_errors
            return JsonResponse(response)

        except DishRestaurantResolutionError as e:
            return JsonResponse({
                'success': False,
                'errors': {f'dish_{e.dish_index}_restaurant': e.message}
            }, status=400)

        except Exception as e:
            logger.error("Failed to update review %s: %s", pk, e, exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Failed to update review: {str(e)}'
            }, status=500)

    def _update_review(self, review, data, restaurant, food_festival):
        basic_info = data.get('basicInfo', {})
        rating_data = data.get('rating', {})

        entry_time = basic_info.get('entryTime') or '12:00'

        review.restaurant = restaurant
        review.food_festival = food_festival
        review.visit_date = basic_info['visitDate']
        review.entry_time = entry_time
        review.party_size = int(basic_info['partySize'])
        review.rating = int(rating_data['overall'])
        review.title = rating_data.get('title', '')
        review.notes = rating_data.get('notes', '')
        if rating_data.get('ambiance'):
            review.metadata['ambiance_rating'] = int(rating_data['ambiance'])
        if rating_data.get('service'):
            review.metadata['service_rating'] = int(rating_data['service'])
        review.is_draft = bool(data.get('is_draft', review.is_draft))
        review.save()

    def _sync_dishes(self, review, dishes_data, user):
        """Update existing dishes, create new ones, delete dishes removed from the payload."""
        image_errors = []
        submitted_ids = set()

        for i, dish_data in enumerate(dishes_data):
            encyclopedia_entry = resolve_encyclopedia_entry(dish_data)
            cost = dish_data.get('cost')
            dish_id = dish_data.get('id')

            review_dish = ReviewDish.objects.filter(id=dish_id, review=review).first() if dish_id else None

            if review_dish is None:
                review_dish = ReviewDish.objects.create(
                    review=review,
                    encyclopedia_entry=encyclopedia_entry,
                    dish_name=dish_data['name'],
                    dish_rating=int(dish_data.get('rating', 50)),
                    notes=dish_data.get('notes', ''),
                    cost=cost if cost else None,
                )
                if review.food_festival_id:
                    dish_restaurant, dish_restaurant_error = resolve_dish_restaurant(dish_data, user)
                    if dish_restaurant_error:
                        raise DishRestaurantResolutionError(i, dish_restaurant_error)
                else:
                    dish_restaurant = review.restaurant
                link_or_create_wishlist_dish(
                    review, dish_data['name'], encyclopedia_entry, dish_restaurant, review.food_festival
                )
            else:
                review_dish.encyclopedia_entry = encyclopedia_entry
                review_dish.dish_name = dish_data['name']
                review_dish.dish_rating = int(dish_data.get('rating', 50))
                review_dish.notes = dish_data.get('notes', '')
                review_dish.cost = cost if cost else None
                review_dish.save()

            submitted_ids.add(review_dish.id)

            image_errors.extend(sync_dish_images(review_dish, dish_data.get('images', []), user))

        review.review_dishes.exclude(id__in=submitted_ids).delete()
        return image_errors
