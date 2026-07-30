import json
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator

from content.services.ai_service import generate_text, AIServiceError

_SYSTEM_PROMPT = (
    "You are an editor for a food review blog. The user will give you a passage from a restaurant review. "
    "Rewrite it to read more smoothly and with more variety, while preserving all specific observations, "
    "opinions, and details. Do not add new information or invented claims. Do not change the author's voice, "
    "tone, or overall meaning.\n\n"
    "Apply these edits:\n"
    "- Vary sentence openers; avoid multiple consecutive sentences that start with 'The'.\n"
    "- Combine short, choppy sentences using em-dashes, subordinate clauses, or appositives instead of "
    "comma-spliced 'and' chains.\n"
    "- Replace flat or generic descriptors (e.g. 'nice', 'real creamy', 'so sweet') with more specific, "
    "vivid word choices that still match what was actually described.\n"
    "- If the passage doesn't already end on a synthesizing thought, add a brief closing sentence that ties "
    "the description together — but only if it can be inferred from details already present, never a new claim.\n"
    "- Fix redundant or awkward phrasing and any grammar errors.\n"
    "- Vary logical connectors instead of relying only on 'but' and 'and'.\n"
    "- Strengthen weak verbs (e.g. 'is', 'has', 'comes with') into more precise ones.\n\n"
    "Return only the rewritten text, no commentary."
)

MAX_TEXT_LENGTH = 5000


def _is_staff(user):
    return user.is_staff


@method_decorator([login_required, user_passes_test(_is_staff)], name='dispatch')
class ReviewAIRewriteApiView(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        text = data.get('text', '').strip()
        if not text:
            return JsonResponse({'error': 'text is required'}, status=400)
        if len(text) > MAX_TEXT_LENGTH:
            return JsonResponse(
                {'error': f'text must be {MAX_TEXT_LENGTH} characters or fewer'},
                status=400,
            )

        try:
            rewritten = generate_text(_SYSTEM_PROMPT, text)
        except AIServiceError:
            return JsonResponse({'error': 'AI service unavailable'}, status=503)

        return JsonResponse({'rewritten': rewritten})
