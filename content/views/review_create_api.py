import json

from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from content.models import Restaurant, Review, ReviewDish, ReviewDraft
from content.views.review_shared import (
    validate_review_data,
    resolve_restaurant,
    resolve_food_festival,
    resolve_dish_restaurant,
    save_review_images,
    save_dish_images,
    link_or_create_wishlist_dish,
    resolve_encyclopedia_entry,
    resolve_menu_item,
    DishRestaurantResolutionError,
)


class ReviewCreateApiView(LoginRequiredMixin, View):
    """
    API endpoint for creating a new review from the modal form.
    Expects JSON data with all review information including dishes and images.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Create a new review with all related data.
        Returns JSON with the created review ID and URL.
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)

        validation_errors = validate_review_data(data, dishes_required=True)
        if validation_errors:
            return JsonResponse({
                'success': False,
                'errors': validation_errors
            }, status=400)

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
            return JsonResponse({
                'success': False,
                'errors': {error_key: target_error}
            }, status=400)

        try:
            with transaction.atomic():
                review = self._create_review(data, restaurant, food_festival, request.user)

                review_images_data = data.get('rating', {}).get('images', [])
                image_errors = save_review_images(review, review_images_data, request.user)

                image_errors.extend(self._create_dishes(review, data.get('dishes', []), request.user))

                draft_id = data.get('draft_id')
                if draft_id:
                    try:
                        draft = ReviewDraft.objects.get(id=draft_id, user=request.user)
                        draft.delete()
                    except ReviewDraft.DoesNotExist:
                        pass  # Draft already deleted or doesn't exist

            response = {
                'success': True,
                'review_id': review.id,
                'review_url': reverse('content:review_detail', kwargs={'pk': review.id})
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
            return JsonResponse({
                'success': False,
                'error': f'Failed to create review: {str(e)}'
            }, status=500)

    def _create_review(self, data, restaurant, food_festival, user):
        """Create the Review instance."""
        basic_info = data.get('basicInfo', {})
        rating_data = data.get('rating', {})

        entry_time = basic_info.get('entryTime')
        if not entry_time:
            entry_time = '12:00'

        metadata = {}

        review = Review.objects.create(
            restaurant=restaurant,
            food_festival=food_festival,
            visit_date=basic_info['visitDate'],
            entry_time=entry_time,
            party_size=int(basic_info['partySize']),
            rating=int(rating_data['overall']),
            title=rating_data.get('title', ''),
            notes=rating_data.get('notes', ''),
            created_by=user,
            metadata=metadata,
            is_draft=bool(data.get('is_draft', False)),
        )

        if rating_data.get('ambiance'):
            review.metadata['ambiance_rating'] = int(rating_data['ambiance'])
        if rating_data.get('service'):
            review.metadata['service_rating'] = int(rating_data['service'])
        review.save()

        return review

    def _create_dishes(self, review, dishes_data, user):
        """Create ReviewDish instances with images. Returns list of image save errors."""
        image_errors = []
        for i, dish_data in enumerate(dishes_data):
            encyclopedia_entry = resolve_encyclopedia_entry(dish_data)

            if review.food_festival_id:
                dish_restaurant, dish_restaurant_error = resolve_dish_restaurant(dish_data, user)
                if dish_restaurant_error:
                    raise DishRestaurantResolutionError(i, dish_restaurant_error)
            else:
                dish_restaurant = review.restaurant

            menu_item = resolve_menu_item(dish_restaurant, dish_data['name'], encyclopedia_entry)

            cost = dish_data.get('cost')
            review_dish = ReviewDish.objects.create(
                review=review,
                menu_item=menu_item,
                dish_rating=int(dish_data.get('rating', 50)),
                notes=dish_data.get('notes', ''),
                cost=cost if cost else None
            )

            link_or_create_wishlist_dish(
                review, dish_data['name'], menu_item.encyclopedia_entry, dish_restaurant, review.food_festival
            )

            image_errors.extend(save_dish_images(review_dish, dish_data.get('images', []), user))

        return image_errors
