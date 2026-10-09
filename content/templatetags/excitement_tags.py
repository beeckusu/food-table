from django import template
from content.models import RestaurantDish

register = template.Library()


@register.simple_tag
def excitement_levels():
    """The selectable excitement levels (1..EXCITEMENT_MAX), for flame pickers."""
    return RestaurantDish.EXCITEMENT_LEVELS
