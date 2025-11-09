from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from content.models import Encyclopedia
import json


def is_staff_user(user):
    """Check if user is staff."""
    return user.is_staff


@method_decorator([login_required, user_passes_test(is_staff_user)], name='dispatch')
class EncyclopediaConvertApiView(View):
    """
    API endpoint for converting a placeholder encyclopedia entry to a full entry.
    Requires authentication and staff permissions.
    """

    def post(self, request, entry_id, *args, **kwargs):
        """
        Convert a placeholder encyclopedia entry to a full entry.

        POST params:
            entry_id: int (URL param) - ID of the encyclopedia entry to convert

        POST body: {
            "description": str (required),
            "cuisine_type": str (optional),
            "dish_category": str (optional),
            "region": str (optional),
            "cultural_significance": str (optional),
            "popular_examples": str (optional),
            "history": str (optional)
        }

        Returns:
            success: bool
            message: str
            encyclopedia: dict with entry details
        """
        try:
            # Parse request body
            data = json.loads(request.body) if request.body else {}

            # Get the encyclopedia entry
            entry = get_object_or_404(Encyclopedia, id=entry_id)

            # Verify entry is currently a placeholder
            if not entry.is_placeholder:
                return JsonResponse({
                    'error': 'Entry is not a placeholder'
                }, status=400)

            # Get description from request data or use existing
            description = data.get('description', entry.description)
            if description:
                description = description.strip()

            # Verify entry has description (required for conversion)
            if not description:
                return JsonResponse({
                    'error': 'Description is required to convert placeholder to full entry'
                }, status=400)

            # Update fields if provided
            entry.description = description

            # Update optional fields if provided
            if 'cuisine_type' in data:
                entry.cuisine_type = data['cuisine_type'].strip() or None
            if 'dish_category' in data:
                entry.dish_category = data['dish_category'].strip() or None
            if 'region' in data:
                entry.region = data['region'].strip() or None
            if 'cultural_significance' in data:
                entry.cultural_significance = data['cultural_significance'].strip()
            if 'popular_examples' in data:
                entry.popular_examples = data['popular_examples'].strip()
            if 'history' in data:
                entry.history = data['history'].strip()

            # Convert to full entry
            entry.is_placeholder = False

            # Validate and save
            try:
                entry.full_clean()
                entry.save()
            except ValidationError as e:
                return JsonResponse({
                    'error': f'Validation error: {str(e)}'
                }, status=400)

            # Return success response
            return JsonResponse({
                'success': True,
                'message': f'Placeholder "{entry.name}" successfully converted to full entry',
                'encyclopedia': {
                    'id': entry.id,
                    'name': entry.name,
                    'slug': entry.slug,
                    'is_placeholder': entry.is_placeholder,
                    'description': entry.description,
                    'cuisine_type': entry.cuisine_type,
                    'dish_category': entry.dish_category,
                    'region': entry.region,
                    'hierarchy': entry.get_hierarchy_breadcrumb(),
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
