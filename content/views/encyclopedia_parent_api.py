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
class EncyclopediaParentApiView(View):
    """
    API endpoint for setting/changing the parent of an Encyclopedia entry.
    Requires authentication and staff permissions.
    """

    def post(self, request, entry_id, *args, **kwargs):
        """
        Set or change the parent of an encyclopedia entry.
        POST body: {"parent_id": <id>} or {"parent_id": null} to remove parent
        """
        try:
            # Parse request body
            data = json.loads(request.body)
            parent_id = data.get('parent_id')

            # Get the encyclopedia entry
            entry = get_object_or_404(Encyclopedia, id=entry_id)

            # Handle parent update
            if parent_id is None:
                # Remove parent
                entry.parent = None
            else:
                # Set new parent
                parent_entry = get_object_or_404(Encyclopedia, id=parent_id)
                entry.parent = parent_entry

            # Save will trigger validation including cycle check
            try:
                entry.save()
            except ValidationError as e:
                return JsonResponse({'error': str(e)}, status=400)

            # Return updated entry info
            return JsonResponse({
                'success': True,
                'entry': {
                    'id': entry.id,
                    'name': entry.name,
                    'slug': entry.slug,
                    'parent': {
                        'id': entry.parent.id,
                        'name': entry.parent.name,
                        'slug': entry.parent.slug,
                    } if entry.parent else None,
                    'ancestors': [
                        {
                            'id': ancestor.id,
                            'name': ancestor.name,
                            'slug': ancestor.slug,
                        }
                        for ancestor in entry.get_ancestors()
                    ],
                    'hierarchy': entry.get_hierarchy_breadcrumb(),
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
