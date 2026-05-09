from django.db import migrations


def populate_restaurants(apps, schema_editor):
    Review = apps.get_model('content', 'Review')
    Restaurant = apps.get_model('content', 'Restaurant')

    seen = {}
    for review in Review.objects.all().order_by('id'):
        name = review.restaurant_name
        location = review.location
        key = (name.strip().lower(), location.strip().lower())
        if key not in seen:
            restaurant, _ = Restaurant.objects.get_or_create(
                name=name,
                location=location,
                defaults={'address': review.address},
            )
            seen[key] = restaurant
        review.restaurant = seen[key]
        review.save(update_fields=['restaurant'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0014_restaurant'),
    ]

    operations = [
        migrations.RunPython(populate_restaurants, migrations.RunPython.noop),
    ]
