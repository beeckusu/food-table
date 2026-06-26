from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0030_restaurantdishreference'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restaurantdish',
            name='source',
        ),
        migrations.RemoveField(
            model_name='restaurantdish',
            name='source_detail',
        ),
    ]
