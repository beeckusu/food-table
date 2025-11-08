from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from content.models import ReviewDish, Encyclopedia
import json


def is_staff_user(user):
    """Check if user is staff."""
    return user.is_staff


@method_decorator([login_required, user_passes_test(is_staff_user)], name='dispatch')
class EncyclopediaCreateApiView(View):
    """
    API endpoint for creating a new Encyclopedia entry.
    Optionally links it to a dish if dish_id is provided.
    Requires authentication and staff permissions.
    """

    def post(self, request, *args, **kwargs):
        """
        Create a new encyclopedia entry and optionally link it to a dish.
        POST body: {
            "name": str (required),
            "description": str (required),
            "cuisine_type": str (optional),
            "dish_category": str (optional),
            "parent_id": int (optional),
            "dish_id": int (optional - if provided, links the dish to the entry)
        }
        """
        try:
            # Parse request body
            data = json.loads(request.body)

            # Extract required fields
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            dish_id = data.get('dish_id')

            # Validate required fields
            if not name:
                return JsonResponse({'error': 'Name is required'}, status=400)
            if not description:
                return JsonResponse({'error': 'Description is required'}, status=400)

            # Get the dish if dish_id provided
            dish = None
            if dish_id:
                dish = get_object_or_404(ReviewDish, id=dish_id)

            # Extract optional fields
            cuisine_type = data.get('cuisine_type', '').strip() or None
            dish_category = data.get('dish_category', '').strip() or None
            region = data.get('region', '').strip() or None
            cultural_significance = data.get('cultural_significance', '').strip()
            popular_examples = data.get('popular_examples', '').strip()
            history = data.get('history', '').strip()
            parent_id = data.get('parent_id')

            # Get parent if provided
            parent = None
            if parent_id:
                try:
                    parent = Encyclopedia.objects.get(id=parent_id)
                except Encyclopedia.DoesNotExist:
                    return JsonResponse({'error': 'Invalid parent entry'}, status=400)

            # Generate slug
            base_slug = slugify(name)
            slug = base_slug
            counter = 1

            # Handle duplicate slugs by appending a number
            while Encyclopedia.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Create the encyclopedia entry
            encyclopedia_entry = Encyclopedia(
                name=name,
                slug=slug,
                description=description,
                cuisine_type=cuisine_type,
                dish_category=dish_category,
                region=region,
                cultural_significance=cultural_significance,
                popular_examples=popular_examples,
                history=history,
                parent=parent,
                created_by=request.user
            )

            # Validate and save
            try:
                encyclopedia_entry.full_clean()
                encyclopedia_entry.save()
            except ValidationError as e:
                return JsonResponse({'error': str(e)}, status=400)

            # Link the dish to the new encyclopedia entry if dish was provided
            if dish:
                dish.encyclopedia_entry = encyclopedia_entry
                dish.save()

            # Return success response
            response_data = {
                'success': True,
                'encyclopedia': {
                    'id': encyclopedia_entry.id,
                    'name': encyclopedia_entry.name,
                    'slug': encyclopedia_entry.slug,
                    'hierarchy': encyclopedia_entry.get_hierarchy_breadcrumb(),
                }
            }

            # Include dish info only if dish was linked
            if dish:
                response_data['dish'] = {
                    'id': dish.id,
                }

            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except IntegrityError as e:
            return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
