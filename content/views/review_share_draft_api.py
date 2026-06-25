import json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from content.models import Image, Review, ReviewDish

PLATFORMS = ('instagram', 'google', 'yelp')
SEGMENT_TYPES = ('shared',) + PLATFORMS
MAX_TEXT_LENGTH = 10000


def _is_staff(user):
    return user.is_staff


def _clean_segment(raw):
    if not isinstance(raw, dict):
        return None
    segment_type = raw.get('type')
    if segment_type not in SEGMENT_TYPES:
        return None
    text = raw.get('text', '')
    if not isinstance(text, str):
        text = ''
    return {'type': segment_type, 'text': text[:MAX_TEXT_LENGTH]}


def _clean_platform_images(raw, valid_image_ids):
    raw = raw if isinstance(raw, dict) else {}
    image_ids = raw.get('image_ids', [])
    if not isinstance(image_ids, list):
        image_ids = []
    return {'image_ids': [i for i in image_ids if isinstance(i, int) and i in valid_image_ids]}


@method_decorator([login_required, user_passes_test(_is_staff)], name='dispatch')
class ReviewShareDraftApiView(View):
    """
    Autosave endpoint for the compose-and-share draft (FT-171 / FT-157).
    Persists into Review.metadata['share_draft'] — no separate model.

    The compose text is an ordered list of segments, each tagged 'shared'
    or a specific platform, so platform-specific snippets can be interleaved
    anywhere within the shared text rather than only appended at the end.
    """

    def post(self, request, pk, *args, **kwargs):
        review = get_object_or_404(Review, pk=pk)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

        segments_raw = data.get('segments', [])
        if not isinstance(segments_raw, list):
            return JsonResponse({'success': False, 'error': 'segments must be a list'}, status=400)
        segments = [s for s in (_clean_segment(item) for item in segments_raw) if s is not None]

        platforms = data.get('platforms', {})
        if not isinstance(platforms, dict):
            return JsonResponse({'success': False, 'error': 'platforms must be an object'}, status=400)

        dish_image_ids = Image.objects.filter(
            content_type=ContentType.objects.get_for_model(ReviewDish),
            object_id__in=review.review_dishes.values_list('id', flat=True),
        ).values_list('id', flat=True)
        valid_image_ids = set(review.images.values_list('id', flat=True)) | set(dish_image_ids)

        share_draft = {
            'segments': segments,
            'platforms': {
                platform: _clean_platform_images(platforms.get(platform), valid_image_ids)
                for platform in PLATFORMS
            },
            'updated_at': timezone.now().isoformat(),
        }

        review.metadata['share_draft'] = share_draft
        review.save(update_fields=['metadata', 'updated_at'])

        return JsonResponse({'success': True, 'share_draft': share_draft})
