import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0015_populate_restaurants'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='review',
            name='content_rev_restaur_4e0d3a_idx',
        ),
        migrations.AlterField(
            model_name='review',
            name='restaurant',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reviews',
                to='content.restaurant',
            ),
        ),
        migrations.RemoveField(
            model_name='review',
            name='restaurant_name',
        ),
        migrations.RemoveField(
            model_name='review',
            name='location',
        ),
        migrations.RemoveField(
            model_name='review',
            name='address',
        ),
    ]
