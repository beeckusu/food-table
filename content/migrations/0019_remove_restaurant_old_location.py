from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0018_populate_restaurant_location_fields'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='restaurant',
            unique_together={('name', 'street_address')},
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='location',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='address',
        ),
    ]
