from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def rating_to_stars(value):
    """
    Convert a 0-100 rating to a visual star display (0-10 stars).

    Args:
        value: Integer rating from 0-100

    Returns:
        HTML string with star icons
    """
    if value is None:
        return mark_safe('<span class="text-muted">No rating</span>')

    try:
        value = int(value)
    except (ValueError, TypeError):
        return mark_safe('<span class="text-muted">No rating</span>')

    # Convert 0-100 to 0-10 scale
    stars = value / 10
    full_stars = int(stars)
    half_star = (stars - full_stars) >= 0.5
    empty_stars = 10 - full_stars - (1 if half_star else 0)

    # Build star HTML using Unicode stars
    html = '<span class="stars" aria-label="{} out of 10 stars">'.format(stars)

    # Full stars
    html += '<span class="text-warning">' + '\u2605' * full_stars + '</span>'

    # Half star
    if half_star:
        html += '<span class="text-warning">\u00BD</span>'

    # Empty stars
    if empty_stars > 0:
        html += '<span class="text-muted">' + '\u2606' * empty_stars + '</span>'

    html += '</span>'

    return mark_safe(html)


@register.filter
def rating_to_stars_value(value):
    """
    Convert a 0-100 rating to a 0-10 scale number.

    Args:
        value: Integer rating from 0-100

    Returns:
        Float value from 0-10
    """
    if value is None:
        return 0

    try:
        value = int(value)
        return round(value / 10, 1)
    except (ValueError, TypeError):
        return 0
