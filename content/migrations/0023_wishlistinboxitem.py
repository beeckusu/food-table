from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0022_restaurant_lat_lng'),
    ]

    operations = [
        migrations.CreateModel(
            name='WishlistInboxItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instagram_url', models.URLField(max_length=500)),
                ('discord_message', models.TextField(blank=True)),
                ('discord_message_id', models.CharField(max_length=100, unique=True)),
                ('discord_channel_id', models.CharField(blank=True, max_length=50)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('processed', models.BooleanField(default=False)),
                ('restaurant', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='inbox_items',
                    to='content.restaurant',
                )),
            ],
            options={
                'ordering': ['-added_at'],
            },
        ),
    ]
