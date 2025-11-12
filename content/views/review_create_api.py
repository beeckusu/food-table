import json
import base64
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType

from content.models import Review, ReviewDish, ReviewDraft, Encyclopedia, Image


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
            # Parse JSON data
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)

        # Validate and extract data
        validation_errors = self._validate_data(data)
        if validation_errors:
            return JsonResponse({
                'success': False,
                'errors': validation_errors
            }, status=400)

        try:
            with transaction.atomic():
                # Create the review
                review = self._create_review(data, request.user)

                # Create review dishes
                self._create_dishes(review, data.get('dishes', []), request.user)

                # Delete draft if provided
                draft_id = data.get('draft_id')
                if draft_id:
                    try:
                        draft = ReviewDraft.objects.get(id=draft_id, user=request.user)
                        draft.delete()
                    except ReviewDraft.DoesNotExist:
                        pass  # Draft already deleted or doesn't exist

            # Return success response
            return JsonResponse({
                'success': True,
                'review_id': review.id,
                'review_url': reverse('content:review_detail', kwargs={'pk': review.id})
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to create review: {str(e)}'
            }, status=500)

    def _validate_data(self, data):
        """Validate required fields and data formats."""
        errors = {}

        # Validate basic info
        basic_info = data.get('basicInfo', {})
        if not basic_info.get('restaurantName'):
            errors['restaurant_name'] = 'Restaurant name is required'

        if not basic_info.get('visitDate'):
            errors['visit_date'] = 'Visit date is required'
        else:
            # Validate date format and not in future
            try:
                visit_date = datetime.strptime(basic_info['visitDate'], '%Y-%m-%d').date()
                if visit_date > datetime.now().date():
                    errors['visit_date'] = 'Visit date cannot be in the future'
            except ValueError:
                errors['visit_date'] = 'Invalid date format'

        # Validate party size
        party_size = basic_info.get('partySize')
        if not party_size or int(party_size) < 1:
            errors['party_size'] = 'Party size must be at least 1'

        # Validate rating
        rating_data = data.get('rating', {})
        overall_rating = rating_data.get('overall')
        if overall_rating is None:
            errors['rating'] = 'Overall rating is required'
        else:
            try:
                rating_val = int(overall_rating)
                if rating_val < 0 or rating_val > 100:
                    errors['rating'] = 'Rating must be between 0 and 100'
            except (ValueError, TypeError):
                errors['rating'] = 'Invalid rating value'

        # Validate dishes (at least one required)
        dishes = data.get('dishes', [])
        if not dishes:
            errors['dishes'] = 'At least one dish is required'
        else:
            for i, dish in enumerate(dishes):
                if not dish.get('name'):
                    errors[f'dish_{i}_name'] = f'Dish {i+1} must have a name'

        return errors

    def _create_review(self, data, user):
        """Create the Review instance."""
        basic_info = data.get('basicInfo', {})
        location_info = data.get('location', {})
        rating_data = data.get('rating', {})

        # Parse entry time
        entry_time = basic_info.get('entryTime')
        if not entry_time:
            # Default to noon if not provided
            entry_time = '12:00'

        # Build location string from city and country
        location_parts = []
        if location_info.get('city'):
            location_parts.append(location_info['city'])
        if location_info.get('country'):
            location_parts.append(location_info['country'])
        location = ', '.join(location_parts) if location_parts else ''

        # Create metadata
        metadata = {}
        if basic_info.get('mealType'):
            metadata['meal_type'] = basic_info['mealType']
        if location_info.get('neighborhood'):
            metadata['neighborhood'] = location_info['neighborhood']

        review = Review.objects.create(
            restaurant_name=basic_info['restaurantName'],
            visit_date=basic_info['visitDate'],
            entry_time=entry_time,
            party_size=int(basic_info['partySize']),
            location=location,
            address=location_info.get('address', ''),
            rating=int(rating_data['overall']),
            title=rating_data.get('title', ''),
            notes=rating_data.get('notes', ''),
            created_by=user,
            metadata=metadata
        )

        # Add ambiance and service ratings to metadata if provided
        if rating_data.get('ambiance'):
            review.metadata['ambiance_rating'] = int(rating_data['ambiance'])
        if rating_data.get('service'):
            review.metadata['service_rating'] = int(rating_data['service'])
        review.save()

        return review

    def _create_dishes(self, review, dishes_data, user):
        """Create ReviewDish instances with images."""
        for dish_data in dishes_data:
            # Get or find encyclopedia entry
            encyclopedia_entry = None
            encyclopedia_ids = dish_data.get('encyclopedia_ids', [])

            print(f"Processing dish: {dish_data.get('name')}")
            print(f"Encyclopedia IDs received: {encyclopedia_ids}")

            if encyclopedia_ids:
                # Use first encyclopedia link (only one allowed per dish)
                try:
                    # Convert id to int in case it's a string
                    entry_id = int(encyclopedia_ids[0]['id'])
                    print(f"Trying to find encyclopedia entry with ID: {entry_id}")
                    encyclopedia_entry = Encyclopedia.objects.get(id=entry_id)
                    print(f"Found encyclopedia entry: {encyclopedia_entry.name}")
                except (Encyclopedia.DoesNotExist, ValueError, KeyError, IndexError) as e:
                    # Log but don't fail - just skip the encyclopedia link
                    print(f"Failed to link encyclopedia entry: {e}")
                    pass

            # Create the review dish
            review_dish = ReviewDish.objects.create(
                review=review,
                encyclopedia_entry=encyclopedia_entry,
                dish_name=dish_data['name'],
                dish_rating=int(dish_data.get('rating', 50)),
                notes=dish_data.get('notes', '')
            )

            # Handle image if provided (base64 data)
            image_data = dish_data.get('image')
            if image_data and image_data.startswith('data:image/'):
                self._save_dish_image(review_dish, image_data, user)

    def _save_dish_image(self, review_dish, image_data, user):
        """Convert base64 image to Image model and attach to dish."""
        try:
            # Parse data URL: data:image/jpeg;base64,/9j/4AAQ...
            format_type, imgstr = image_data.split(';base64,')
            ext = format_type.split('/')[-1]  # jpeg, png, webp

            # Decode base64
            image_file = ContentFile(
                base64.b64decode(imgstr),
                name=f'dish_{uuid.uuid4()}.{ext}'
            )

            # Create Image instance
            content_type = ContentType.objects.get_for_model(ReviewDish)
            image = Image.objects.create(
                image=image_file,
                content_type=content_type,
                object_id=review_dish.id,
                uploaded_by=user,
                caption=review_dish.dish_name,
                alt_text=f'Photo of {review_dish.dish_name}'
            )

        except Exception as e:
            # Log error but don't fail the whole submission
            print(f"Error saving dish image: {e}")
