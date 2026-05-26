from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0023_wishlistinboxitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiUsageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.CharField(max_length=50)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='apiusagelog',
            index=models.Index(fields=['endpoint', 'timestamp'], name='content_apiusagelog_ep_ts_idx'),
        ),
    ]
