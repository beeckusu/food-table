import json
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from content.models import ReviewDraft


class ReviewDraftSaveApiView(LoginRequiredMixin, View):
    """
    API endpoint for saving/updating review drafts.
    POST to create or update a draft.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Save or update a review draft.
        Creates a new draft if draft_id is not provided or doesn't exist.
        Updates existing draft if draft_id is valid.
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)

        draft_id = data.get('draft_id')
        step = data.get('step', 'basic-info')
        form_data = data.get('data', {})

        try:
            if draft_id:
                # Try to update existing draft
                try:
                    draft = ReviewDraft.objects.get(id=draft_id, user=request.user)
                    draft.step = step
                    draft.data = form_data
                    draft.save()
                except ReviewDraft.DoesNotExist:
                    # Draft doesn't exist, create new one
                    draft = ReviewDraft.objects.create(
                        user=request.user,
                        step=step,
                        data=form_data
                    )
            else:
                # Check if user already has a draft
                draft = ReviewDraft.get_latest_for_user(request.user)
                if draft:
                    # Update existing draft
                    draft.step = step
                    draft.data = form_data
                    draft.save()
                else:
                    # Create new draft
                    draft = ReviewDraft.objects.create(
                        user=request.user,
                        step=step,
                        data=form_data
                    )

            return JsonResponse({
                'success': True,
                'draft_id': str(draft.id),
                'updated_at': draft.updated_at.isoformat(),
                'age_display': draft.age_display
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to save draft: {str(e)}'
            }, status=500)


class ReviewDraftRetrieveApiView(LoginRequiredMixin, View):
    """
    API endpoint for retrieving the latest review draft.
    GET to retrieve the most recent non-expired draft.
    """

    def get(self, request, *args, **kwargs):
        """
        Retrieve the latest non-expired draft for the current user.
        Returns draft data or null if no draft exists.
        """
        draft = ReviewDraft.get_latest_for_user(request.user)

        if not draft:
            return JsonResponse({
                'success': True,
                'draft': None
            })

        return JsonResponse({
            'success': True,
            'draft': {
                'id': str(draft.id),
                'step': draft.step,
                'data': draft.data,
                'created_at': draft.created_at.isoformat(),
                'updated_at': draft.updated_at.isoformat(),
                'age_display': draft.age_display,
                'is_expired': draft.is_expired
            }
        })


class ReviewDraftDeleteApiView(LoginRequiredMixin, View):
    """
    API endpoint for deleting a review draft.
    DELETE to remove a specific draft.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def delete(self, request, draft_id=None, *args, **kwargs):
        """
        Delete a specific draft by ID.
        Only allows deletion of drafts owned by the current user.
        """
        if not draft_id:
            return JsonResponse({
                'success': False,
                'error': 'Draft ID is required'
            }, status=400)

        try:
            draft = ReviewDraft.objects.get(id=draft_id, user=request.user)
            draft.delete()

            return JsonResponse({
                'success': True,
                'message': 'Draft deleted successfully'
            })

        except ReviewDraft.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Draft not found or you do not have permission to delete it'
            }, status=404)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to delete draft: {str(e)}'
            }, status=500)

    def post(self, request, draft_id=None, *args, **kwargs):
        """Support POST for browsers that don't support DELETE."""
        return self.delete(request, draft_id, *args, **kwargs)
