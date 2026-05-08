import re
from django import template
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe

register = template.Library()

_HTML_RE = re.compile(r'<[a-zA-Z]')


@register.filter(is_safe=True)
def rtf(value):
    """Render a field that may contain Quill HTML or legacy plain text.

    HTML content (from Quill) is returned as-is (marked safe).
    Plain text falls back to linebreaks for backward compat.
    """
    if not value:
        return ''
    if _HTML_RE.search(value):
        return mark_safe(value)
    return mark_safe(linebreaks(value))
