from django import template
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

register = template.Library()


@register.inclusion_tag('components/admin_edit_button.html', takes_context=True)
def admin_edit_button(context, obj, button_text="Edit"):
    """
    Renders an edit button linking to Django admin for the given object.
    Only visible to staff users.

    Args:
        context: Template context (automatically passed)
        obj: The model instance to generate an admin edit link for
        button_text: Text to display on the button (default: "Edit")

    Returns:
        Dictionary with button context variables
    """
    user = context['request'].user

    if not user.is_staff:
        return {'show_button': False}

    content_type = ContentType.objects.get_for_model(obj)
    admin_url = reverse(
        f'admin:{content_type.app_label}_{content_type.model}_change',
        args=[obj.pk]
    )

    return {
        'show_button': True,
        'admin_url': admin_url,
        'button_text': button_text,
        'object_name': content_type.model
    }
