import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0032_foodfestival_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='restaurantdish',
            name='restaurantdish_exactly_one_target',
        ),
        migrations.AlterField(
            model_name='restaurantdish',
            name='restaurant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dishes', to='content.restaurant'),
        ),
        migrations.AlterField(
            model_name='restaurantdish',
            name='food_festival',
            field=models.ForeignKey(blank=True, help_text='Set when this dish was tried at the restaurant as part of a food festival', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dishes', to='content.foodfestival'),
        ),
    ]
