import json
import logging

from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from content.models import Encyclopedia

logger = logging.getLogger(__name__)


def _is_staff(user):
    return user.is_staff


@method_decorator([login_required, user_passes_test(_is_staff)], name='dispatch')
class EncyclopediaEditApiView(View):

    def patch(self, request, entry_id, *args, **kwargs):
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        entry = get_object_or_404(Encyclopedia, id=entry_id)

        if 'name' in data:
            new_name = data['name'].strip()
            if not new_name:
                return JsonResponse({'error': 'Name cannot be empty'}, status=400)
            if new_name != entry.name:
                base_slug = slugify(new_name)
                slug = base_slug
                counter = 1
                while Encyclopedia.objects.filter(slug=slug).exclude(pk=entry.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                entry.name = new_name
                entry.slug = slug

        if 'description' in data:
            entry.description = data['description'].strip()
            if entry.is_placeholder and entry.description:
                entry.is_placeholder = False

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

        try:
            entry.full_clean()
            entry.save()
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)

        return JsonResponse({
            'success': True,
            'encyclopedia': {
                'id': entry.id,
                'name': entry.name,
                'slug': entry.slug,
                'description': entry.description,
                'cuisine_type': entry.cuisine_type,
                'dish_category': entry.dish_category,
                'region': entry.region,
            }
        })
