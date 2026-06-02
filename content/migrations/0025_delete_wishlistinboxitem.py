from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0024_apiusagelog'),
    ]

    operations = [
        migrations.DeleteModel(
            name='WishlistInboxItem',
        ),
    ]
