from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from content.models import Encyclopedia
import json


def is_staff_user(user):
    """Check if user is staff."""
    return user.is_staff


@method_decorator([login_required, user_passes_test(is_staff_user)], name='dispatch')
class EncyclopediaQuickCreateApiView(View):
    """
    API endpoint for quickly creating placeholder Encyclopedia entries.
    Used for inline creation from the similar dishes selection interface.
    Requires authentication and staff permissions.
    """

    def post(self, request, *args, **kwargs):
        """
        Create a new placeholder encyclopedia entry.
        POST body: {
            "name": str (required),
            "source_entry_id": int (optional - if provided, links as similar dish)
        }
        """
        try:
            # Parse request body
            data = json.loads(request.body)

            # Extract fields
            name = data.get('name', '').strip()
            source_entry_id = data.get('source_entry_id')

            # Validate required field
            if not name:
                return JsonResponse({'error': 'Name is required'}, status=400)

            # Check for duplicate name
            if Encyclopedia.objects.filter(name__iexact=name).exists():
                return JsonResponse({
                    'error': f'An encyclopedia entry with the name "{name}" already exists'
                }, status=400)

            # Generate slug
            base_slug = slugify(name)
            slug = base_slug
            counter = 1

            # Handle duplicate slugs by appending a number
            while Encyclopedia.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Create the placeholder encyclopedia entry
            encyclopedia_entry = Encyclopedia(
                name=name,
                slug=slug,
                description='',  # Empty description for placeholder
                is_placeholder=True,  # Mark as placeholder
                created_by=request.user
            )

            # Validate and save
            try:
                encyclopedia_entry.full_clean()
                encyclopedia_entry.save()
            except ValidationError as e:
                return JsonResponse({'error': str(e)}, status=400)

            # Link to source entry as similar dish if provided
            if source_entry_id:
                try:
                    source_entry = Encyclopedia.objects.get(id=source_entry_id)
                    # Add the new placeholder to the source entry's similar dishes
                    # Since similar_dishes is symmetrical, this also adds source to the placeholder's similar dishes
                    source_entry.similar_dishes.add(encyclopedia_entry)
                except Encyclopedia.DoesNotExist:
                    # Source entry not found, but we still created the placeholder successfully
                    pass

            # Return success response with minimal data for widget integration
            return JsonResponse({
                'success': True,
                'entry': {
                    'id': encyclopedia_entry.id,
                    'name': encyclopedia_entry.name,
                    'slug': encyclopedia_entry.slug,
                    'is_placeholder': encyclopedia_entry.is_placeholder,
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except IntegrityError as e:
            return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
