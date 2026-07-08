import json
import logging

from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from content.models import Review, ReviewDish
from content.views.review_shared import (
    validate_review_data,
    resolve_restaurant,
    sync_review_images,
    sync_dish_image,
    link_or_create_wishlist_dish,
    resolve_encyclopedia_entry,
)

logger = logging.getLogger(__name__)


class ReviewEditDataApiView(LoginRequiredMixin, View):
    """Returns an existing review's data pre-shaped to match the review modal's formData structure."""

    def get(self, request, pk, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        try:
            review = Review.objects.select_related('restaurant').prefetch_related(
                'review_dishes__encyclopedia_entry', 'review_dishes__images', 'images'
            ).get(pk=pk)
        except Review.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Review not found'}, status=404)

        restaurant = review.restaurant

        dishes = []
        for dish in review.review_dishes.all():
            dish_image = dish.images.first()
            dishes.append({
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
                'image': {'id': dish_image.id, 'src': dish_image.image.url} if dish_image else None,
            })

        data = {
            'basicInfo': {
                'visitDate': review.visit_date.isoformat(),
                'partySize': review.party_size,
                'entryTime': review.entry_time.strftime('%H:%M') if review.entry_time else '',
            },
            'restaurant': {
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
            },
            'rating': {
                'overall': review.rating,
                'title': review.title or '',
                'notes': review.notes or '',
                'ambiance': review.metadata.get('ambiance_rating', 50),
                'service': review.metadata.get('service_rating', 50),
                'images': [{'id': img.id, 'src': img.image.url} for img in review.images.all()],
            },
            'dishes': dishes,
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

        restaurant, restaurant_error = resolve_restaurant(data.get('restaurant', {}), request.user)
        if restaurant_error:
            return JsonResponse({'success': False, 'errors': {'restaurant': restaurant_error}}, status=400)

        try:
            with transaction.atomic():
                self._update_review(review, data, restaurant)

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

        except Exception as e:
            logger.error("Failed to update review %s: %s", pk, e, exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Failed to update review: {str(e)}'
            }, status=500)

    def _update_review(self, review, data, restaurant):
        basic_info = data.get('basicInfo', {})
        rating_data = data.get('rating', {})

        entry_time = basic_info.get('entryTime') or '12:00'

        review.restaurant = restaurant
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
        review.save()

    def _sync_dishes(self, review, dishes_data, user):
        """Update existing dishes, create new ones, delete dishes removed from the payload."""
        image_errors = []
        submitted_ids = set()

        for dish_data in dishes_data:
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
                link_or_create_wishlist_dish(review, dish_data['name'], encyclopedia_entry)
            else:
                review_dish.encyclopedia_entry = encyclopedia_entry
                review_dish.dish_name = dish_data['name']
                review_dish.dish_rating = int(dish_data.get('rating', 50))
                review_dish.notes = dish_data.get('notes', '')
                review_dish.cost = cost if cost else None
                review_dish.save()

            submitted_ids.add(review_dish.id)

            error = sync_dish_image(
                review_dish,
                dish_data.get('existing_image_id'),
                bool(dish_data.get('remove_image')),
                dish_data.get('image'),
                user,
            )
            if error:
                image_errors.append(error)

        review.review_dishes.exclude(id__in=submitted_ids).delete()
        return image_errors
