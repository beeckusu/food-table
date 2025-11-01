from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from content.models import ReviewDish, Image


def is_staff_user(user):
    """Check if user is staff."""
    return user.is_staff


@method_decorator([login_required, user_passes_test(is_staff_user)], name='dispatch')
class DishImageUploadApiView(View):
    """
    API endpoint for uploading images to a ReviewDish.
    Requires authentication and staff permissions.
    """

    def post(self, request, dish_id, *args, **kwargs):
        """
        Upload an image to a dish.
        POST body (multipart/form-data):
            - image: image file (required)
            - caption: optional caption
            - alt_text: optional alt text
            - order: optional order (defaults to 0)
        """
        try:
            # Get the dish
            dish = get_object_or_404(ReviewDish, id=dish_id)

            # Get the uploaded file
            image_file = request.FILES.get('image')
            if not image_file:
                return JsonResponse({'error': 'No image file provided'}, status=400)

            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                return JsonResponse({
                    'error': f'Invalid file type. Allowed types: JPEG, PNG, GIF, WebP'
                }, status=400)

            # Validate file size (10MB max)
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            if image_file.size > max_size:
                return JsonResponse({
                    'error': f'File too large. Maximum size is 10MB'
                }, status=400)

            # Get optional fields
            caption = request.POST.get('caption', '')
            alt_text = request.POST.get('alt_text', '')
            order = request.POST.get('order', 0)

            # Create the Image instance
            content_type = ContentType.objects.get_for_model(ReviewDish)
            image = Image.objects.create(
                image=image_file,
                caption=caption,
                alt_text=alt_text,
                order=order,
                content_type=content_type,
                object_id=dish.id,
                uploaded_by=request.user
            )

            # Return success response with image data
            return JsonResponse({
                'success': True,
                'image': {
                    'id': image.id,
                    'url': image.image.url,
                    'caption': image.caption,
                    'alt_text': image.alt_text,
                    'order': image.order,
                    'uploaded_at': image.uploaded_at.isoformat(),
                }
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
