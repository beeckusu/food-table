import json
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)
from django.views import View
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator

from content.services.ai_service import generate_text, AIServiceError

_SYSTEM_PROMPT = """You are an encyclopedia writer for a food blog. Given a dish name, generate accurate content for each field. Return ONLY valid JSON (no markdown code blocks, no commentary, no preamble) with exactly these keys:

- "name": The dish name as provided. Optionally add the native script in parentheses for well-known non-English dishes (e.g. "Dan Dan Noodles (担担面)").
- "description": 2–4 paragraphs describing the dish's appearance, texture, flavours, and defining characteristics. Plain prose, no headers. Separate paragraphs with \\n\\n.
- "similar_dishes_globally": A comma-separated list of 3–6 globally similar dishes (dish names only, e.g. "Ma Jiang Mian, Tantanmen, Xiao Mian").
- "cuisine_type": A single cuisine label (e.g. "Sichuan", "Japanese", "French", "Cantonese", "Korean", "Southern American"). Short and specific.
- "dish_category": A single category noun (e.g. "Noodles", "Dessert", "Entrée", "Soup", "Appetizer", "Pastry", "Side dish", "Snack").
- "region": A short place/time label only — no full sentences, 6 words or fewer (e.g. "Sichuan Province, China", "Late 19th century France", "Southern United States", "Northern China", "Korea, Joseon Dynasty").
- "cultural_significance": 2–3 paragraphs on cultural importance, traditions, and regional identity. Plain prose, no headers. Separate paragraphs with \\n\\n.
- "popular_examples": Newline-separated list of 5–8 items mixing specific dish variations AND notable restaurants or chains. Format: "Name – Description." No bullet characters. Example:\\nTexas Brisket – Beef brisket smoked low and slow with a simple salt-and-pepper rub.\\nOlive Garden – Known for unlimited breadsticks served with pasta.
- "history": Newline-separated chronological list of 5–8 events. Format: "Time Period – Description." No bullet characters. Example:\\nMid-1800s – Street vendors in Sichuan sell Dan Dan Noodles using shoulder poles.\\n1900s – Restaurant versions become richer with sesame paste and heavier sauces.

Return only the JSON object. No markdown, no commentary."""

MAX_DISH_NAME_LENGTH = 200


def _is_staff(user):
    return user.is_staff


@method_decorator([login_required, user_passes_test(_is_staff)], name='dispatch')
class EncyclopediaAIPrefillApiView(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        dish_name = data.get('dish_name', '').strip()
        if not dish_name:
            return JsonResponse({'error': 'dish_name is required'}, status=400)
        if len(dish_name) > MAX_DISH_NAME_LENGTH:
            return JsonResponse(
                {'error': f'dish_name must be {MAX_DISH_NAME_LENGTH} characters or fewer'},
                status=400,
            )

        try:
            raw = generate_text(_SYSTEM_PROMPT, dish_name)
        except AIServiceError as e:
            logger.error("Encyclopedia AI prefill failed for %r: %s", dish_name, e)
            return JsonResponse({'error': 'AI service unavailable'}, status=503)

        try:
            fields = json.loads(raw)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'AI returned malformed response'}, status=503)

        return JsonResponse({'success': True, 'fields': fields})
