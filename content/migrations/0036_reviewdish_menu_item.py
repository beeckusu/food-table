import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0035_menuitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewdish',
            name='menu_item',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='review_dishes',
                to='content.menuitem',
                help_text="The restaurant-scoped dish being reviewed, shared with every other review of it.",
            ),
        ),
    ]
