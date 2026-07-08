import base64
import uuid
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType

from content.models import Restaurant, Encyclopedia, Image, ApiUsageLog

logger = logging.getLogger(__name__)


def validate_review_data(data, dishes_required=True):
    """Validate required fields and data formats shared by create/update."""
    errors = {}

    basic_info = data.get('basicInfo', {})
    if not basic_info.get('visitDate'):
        errors['visit_date'] = 'Visit date is required'
    else:
        try:
            visit_date = datetime.strptime(basic_info['visitDate'], '%Y-%m-%d').date()
            if visit_date > datetime.now(tz=ZoneInfo('America/New_York')).date():
                errors['visit_date'] = 'Visit date cannot be in the future'
        except ValueError:
            errors['visit_date'] = 'Invalid date format'

    party_size = basic_info.get('partySize')
    if not party_size or int(party_size) < 1:
        errors['party_size'] = 'Party size must be at least 1'

    restaurant_data = data.get('restaurant', {})
    mode = restaurant_data.get('mode', 'search')
    if mode == 'new':
        if not (restaurant_data.get('name') or '').strip():
            errors['restaurant'] = 'Restaurant name is required'
        elif restaurant_data.get('isPopUp') and not (restaurant_data.get('website') or '').strip():
            errors['restaurant'] = 'Website is required for pop-up restaurants'
    else:
        if not restaurant_data.get('id') and not (restaurant_data.get('name') or '').strip():
            errors['restaurant'] = 'Please select a restaurant or add a new one'

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

    dishes = data.get('dishes', [])
    if dishes_required and not dishes:
        errors['dishes'] = 'At least one dish is required'
    else:
        for i, dish in enumerate(dishes):
            if not dish.get('name'):
                errors[f'dish_{i}_name'] = f'Dish {i+1} must have a name'

    return errors


def resolve_restaurant(restaurant_data, user):
    """
    Resolve the Restaurant instance for a review from the restaurant picker payload.
    Returns (restaurant, error_message). error_message is None on success.
    """
    mode = restaurant_data.get('mode', 'search')

    if mode == 'new':
        name = (restaurant_data.get('name') or '').strip()
        street_address = (restaurant_data.get('address') or '').strip()
        restaurant, created = Restaurant.objects.get_or_create(
            name=name,
            street_address=street_address,
            defaults={
                'city': (restaurant_data.get('city') or '').strip(),
                'province': (restaurant_data.get('province') or '').strip(),
                'country': (restaurant_data.get('country') or '').strip(),
                'postal_code': (restaurant_data.get('postalCode') or '').strip(),
                'is_pop_up': bool(restaurant_data.get('isPopUp')),
                'website': (restaurant_data.get('website') or '').strip(),
                'google_place_id': (restaurant_data.get('googlePlaceId') or '').strip(),
                'visited': True,
                'created_by': user,
            },
        )
        if not created and not restaurant.visited:
            restaurant.visited = True
            restaurant.save(update_fields=['visited'])
        if created and restaurant_data.get('placesSessionUsed'):
            ApiUsageLog.objects.create(endpoint='places')
        return restaurant, None

    restaurant_id = restaurant_data.get('id')
    if restaurant_id:
        try:
            restaurant = Restaurant.objects.get(pk=restaurant_id)
        except (Restaurant.DoesNotExist, ValueError, TypeError):
            return None, 'Selected restaurant could not be found'
        if not restaurant.visited:
            restaurant.visited = True
            restaurant.save(update_fields=['visited'])
        return restaurant, None

    # No id selected but a name was typed (legacy "quick create by name" path)
    name = (restaurant_data.get('name') or '').strip()
    if not name:
        return None, 'Please select a restaurant or add a new one'
    restaurant, created = Restaurant.objects.get_or_create(
        name=name,
        street_address='',
        defaults={'visited': True, 'created_by': user},
    )
    if not created and not restaurant.visited:
        restaurant.visited = True
        restaurant.save(update_fields=['visited'])
    return restaurant, None


def save_review_images(review, images_data, user):
    """Save base64-encoded images attached to the review itself. Returns list of error strings."""
    errors = []
    for image_data in images_data:
        if not (isinstance(image_data, str) and image_data.startswith('data:image/')):
            continue
        try:
            format_type, imgstr = image_data.split(';base64,')
            ext = format_type.split('/')[-1]

            image_file = ContentFile(
                base64.b64decode(imgstr),
                name=f'review_{uuid.uuid4()}.{ext}'
            )

            content_type = ContentType.objects.get_for_model(review)
            Image.objects.create(
                image=image_file,
                content_type=content_type,
                object_id=review.id,
                uploaded_by=user,
            )
        except Exception as e:
            logger.error("Error saving image for review %s: %s", review.id, e, exc_info=True)
            errors.append(f"A review photo failed to save: {e}")
    return errors


def save_dish_image(review_dish, image_data, user):
    """Convert base64 image to Image model and attach to dish. Returns error string or None."""
    try:
        format_type, imgstr = image_data.split(';base64,')
        ext = format_type.split('/')[-1]  # jpeg, png, webp

        image_file = ContentFile(
            base64.b64decode(imgstr),
            name=f'dish_{uuid.uuid4()}.{ext}'
        )

        content_type = ContentType.objects.get_for_model(review_dish)
        Image.objects.create(
            image=image_file,
            content_type=content_type,
            object_id=review_dish.id,
            uploaded_by=user,
            caption=review_dish.dish_name,
            alt_text=f'Photo of {review_dish.dish_name}'
        )
        return None

    except Exception as e:
        logger.error("Error saving dish image for dish %s: %s", review_dish.id, e, exc_info=True)
        return f"Image for '{review_dish.dish_name}' failed to save: {e}"


def link_or_create_wishlist_dish(review, dish_name, encyclopedia_entry):
    """Promote an existing wishlist entry to 'had', or create a new RestaurantDish record."""
    from content.models import RestaurantDish, RestaurantDishReference

    wishlist_dish = RestaurantDish.objects.filter(
        restaurant=review.restaurant,
        dish_name=dish_name,
        status=RestaurantDish.STATUS_WISHLIST,
    ).first()
    if wishlist_dish:
        wishlist_dish.status = RestaurantDish.STATUS_HAD
        wishlist_dish.review = review
        if encyclopedia_entry:
            wishlist_dish.encyclopedia_entry = encyclopedia_entry
        wishlist_dish.save()
        return wishlist_dish

    new_dish = RestaurantDish.objects.create(
        restaurant=review.restaurant,
        dish_name=dish_name,
        encyclopedia_entry=encyclopedia_entry,
        status=RestaurantDish.STATUS_HAD,
        review=review,
    )
    RestaurantDishReference.objects.create(
        dish=new_dish,
        source='review',
    )
    return new_dish


def sync_review_images(review, images_data, user):
    """
    Reconcile review-level images on update: delete existing images the user removed,
    save any newly-added base64 images. Returns list of error strings.
    """
    content_type = ContentType.objects.get_for_model(review)
    kept_ids = {
        int(item['id']) for item in images_data
        if isinstance(item, dict) and item.get('id')
    }
    Image.objects.filter(content_type=content_type, object_id=review.id).exclude(id__in=kept_ids).delete()

    new_sources = [
        item.get('src') for item in images_data
        if isinstance(item, dict) and not item.get('id')
    ]
    return save_review_images(review, new_sources, user)


def sync_dish_image(review_dish, existing_image_id, remove_image, new_image_data, user):
    """Reconcile a dish's single image on update: remove/replace/keep. Returns error string or None."""
    has_new_image = bool(new_image_data and new_image_data.startswith('data:image/'))

    if (remove_image or has_new_image) and existing_image_id:
        content_type = ContentType.objects.get_for_model(review_dish)
        Image.objects.filter(content_type=content_type, object_id=review_dish.id, id=existing_image_id).delete()

    if has_new_image:
        return save_dish_image(review_dish, new_image_data, user)
    return None


def resolve_encyclopedia_entry(dish_data):
    """Resolve the (optional) encyclopedia entry linked to a dish payload."""
    encyclopedia_ids = dish_data.get('encyclopedia_ids', [])
    if not encyclopedia_ids:
        return None
    try:
        entry_id = int(encyclopedia_ids[0]['id'])
        return Encyclopedia.objects.get(id=entry_id)
    except (Encyclopedia.DoesNotExist, ValueError, KeyError, IndexError) as e:
        logger.warning("Failed to link encyclopedia entry: %s", e)
        return None
