import django.db.models.deletion
from django.db import migrations, models


def populate_references(apps, schema_editor):
    RestaurantDish = apps.get_model('content', 'RestaurantDish')
    RestaurantDishReference = apps.get_model('content', 'RestaurantDishReference')
    for dish in RestaurantDish.objects.exclude(source='', source_detail=''):
        RestaurantDishReference.objects.create(
            dish=dish,
            source=dish.source,
            source_detail=dish.source_detail,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0029_recompute_encyclopedia_search_vector'),
    ]

    operations = [
        migrations.CreateModel(
            name='RestaurantDishReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(blank=True, max_length=255)),
                ('source_detail', models.CharField(blank=True, max_length=255)),
                ('dish', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='references', to='content.restaurantdish')),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.RunPython(populate_references, migrations.RunPython.noop),
    ]
