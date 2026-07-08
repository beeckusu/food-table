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
    save_review_images,
    save_dish_image,
    link_or_create_wishlist_dish,
    resolve_encyclopedia_entry,
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

        restaurant, restaurant_error = resolve_restaurant(data.get('restaurant', {}), request.user)
        if restaurant_error:
            return JsonResponse({
                'success': False,
                'errors': {'restaurant': restaurant_error}
            }, status=400)

        try:
            with transaction.atomic():
                review = self._create_review(data, restaurant, request.user)

                review_images_data = data.get('rating', {}).get('images', [])
                review_image_srcs = [
                    img.get('src') if isinstance(img, dict) else img
                    for img in review_images_data
                ]
                image_errors = save_review_images(review, review_image_srcs, request.user)

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

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to create review: {str(e)}'
            }, status=500)

    def _create_review(self, data, restaurant, user):
        """Create the Review instance."""
        basic_info = data.get('basicInfo', {})
        rating_data = data.get('rating', {})

        entry_time = basic_info.get('entryTime')
        if not entry_time:
            entry_time = '12:00'

        metadata = {}

        review = Review.objects.create(
            restaurant=restaurant,
            visit_date=basic_info['visitDate'],
            entry_time=entry_time,
            party_size=int(basic_info['partySize']),
            rating=int(rating_data['overall']),
            title=rating_data.get('title', ''),
            notes=rating_data.get('notes', ''),
            created_by=user,
            metadata=metadata
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
        for dish_data in dishes_data:
            encyclopedia_entry = resolve_encyclopedia_entry(dish_data)

            cost = dish_data.get('cost')
            review_dish = ReviewDish.objects.create(
                review=review,
                encyclopedia_entry=encyclopedia_entry,
                dish_name=dish_data['name'],
                dish_rating=int(dish_data.get('rating', 50)),
                notes=dish_data.get('notes', ''),
                cost=cost if cost else None
            )

            link_or_create_wishlist_dish(review, dish_data['name'], encyclopedia_entry)

            image_data = dish_data.get('image')
            if image_data and image_data.startswith('data:image/'):
                error = save_dish_image(review_dish, image_data, user)
                if error:
                    image_errors.append(error)

        return image_errors
