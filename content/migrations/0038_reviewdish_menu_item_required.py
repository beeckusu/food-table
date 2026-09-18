import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0037_backfill_menu_items'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reviewdish',
            name='dish_name',
        ),
        migrations.RemoveField(
            model_name='reviewdish',
            name='encyclopedia_entry',
        ),
        migrations.AlterField(
            model_name='reviewdish',
            name='menu_item',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='review_dishes',
                to='content.menuitem',
                help_text="The restaurant-scoped dish being reviewed, shared with every other review of it.",
            ),
        ),
    ]
