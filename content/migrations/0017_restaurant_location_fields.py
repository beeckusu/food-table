from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0016_finalize_restaurant'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='street_address',
            field=models.CharField(blank=True, max_length=255, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='restaurant',
            name='city',
            field=models.CharField(blank=True, max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='restaurant',
            name='province',
            field=models.CharField(blank=True, max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='restaurant',
            name='country',
            field=models.CharField(blank=True, max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='restaurant',
            name='postal_code',
            field=models.CharField(blank=True, max_length=20, default=''),
            preserve_default=False,
        ),
    ]
