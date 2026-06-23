from django.contrib.postgres.search import SearchVector
from django.db import migrations


def recompute_search_vector(apps, schema_editor):
    """
    Recompute search_vector for all existing Encyclopedia entries now that
    cuisine_type and dish_category are included (FT-176).
    """
    Encyclopedia = apps.get_model('content', 'Encyclopedia')

    for entry in Encyclopedia.objects.all():
        Encyclopedia.objects.filter(pk=entry.pk).update(
            search_vector=(
                SearchVector('name', weight='A')
                + SearchVector('cuisine_type', weight='B')
                + SearchVector('dish_category', weight='B')
                + SearchVector('description', weight='B')
            )
        )


def reverse_recompute_search_vector(apps, schema_editor):
    """
    Restore search_vector to name + description only (reverse operation).
    """
    Encyclopedia = apps.get_model('content', 'Encyclopedia')

    for entry in Encyclopedia.objects.all():
        Encyclopedia.objects.filter(pk=entry.pk).update(
            search_vector=SearchVector('name', weight='A') + SearchVector('description', weight='B')
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0028_restaurant_pop_up_website'),
    ]

    operations = [
        migrations.RunPython(recompute_search_vector, reverse_recompute_search_vector),
    ]
