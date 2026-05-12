from django.db import migrations


def split_location(apps, schema_editor):
    Restaurant = apps.get_model('content', 'Restaurant')
    Review = apps.get_model('content', 'Review')

    # Populate new fields from old ones
    for restaurant in Restaurant.objects.all():
        restaurant.street_address = restaurant.address or ''

        parts = [p.strip() for p in (restaurant.location or '').split(',') if p.strip()]
        if len(parts) == 1:
            restaurant.city = parts[0]
        elif len(parts) == 2:
            restaurant.city = parts[0]
            restaurant.country = parts[1]
        elif len(parts) >= 3:
            restaurant.city = parts[0]
            restaurant.province = ', '.join(parts[1:-1])
            restaurant.country = parts[-1]

        restaurant.save(update_fields=['street_address', 'city', 'province', 'country'])

    # Deduplicate by (name, street_address): keep lowest id, re-point reviews, delete duplicates
    seen = {}
    for restaurant in Restaurant.objects.order_by('id'):
        key = (restaurant.name, restaurant.street_address)
        if key in seen:
            canonical = seen[key]
            Review.objects.filter(restaurant=restaurant).update(restaurant=canonical)
            restaurant.delete()
        else:
            seen[key] = restaurant


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0017_restaurant_location_fields'),
    ]

    operations = [
        migrations.RunPython(split_location, migrations.RunPython.noop),
    ]
