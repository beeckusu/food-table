import html
import logging
import re

import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, JsonResponse
from django.views import View

logger = logging.getLogger(__name__)

INSTAGRAM_URL_RE = re.compile(
    r'^https?://(?:www\.)?instagram\.com/(?:reel|p)/[A-Za-z0-9_-]+/?(?:\?.*)?$',
    re.IGNORECASE,
)
OG_DESCRIPTION_TAG_RE = re.compile(r'<meta[^>]*property=["\']og:description["\'][^>]*>', re.IGNORECASE)
CONTENT_ATTR_RE = re.compile(r'content=["\']([^"\']*)["\']', re.IGNORECASE)


class InstagramPreviewApiView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()

        url = (request.GET.get('url') or '').strip()
        if not INSTAGRAM_URL_RE.match(url):
            return JsonResponse({'success': False, 'error': 'Not a valid Instagram post URL'}, status=400)

        try:
            response = requests.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; FoodTableBot/1.0)'},
                timeout=5,
            )
        except requests.RequestException:
            logger.exception('Failed to fetch Instagram preview for %s', url)
            return JsonResponse({'success': False, 'error': 'Could not reach Instagram'})

        tag_match = OG_DESCRIPTION_TAG_RE.search(response.text)
        content_match = CONTENT_ATTR_RE.search(tag_match.group(0)) if tag_match else None
        if not content_match:
            return JsonResponse({'success': False, 'error': 'No description found'})

        return JsonResponse({'success': True, 'description': html.unescape(content_match.group(1))})
