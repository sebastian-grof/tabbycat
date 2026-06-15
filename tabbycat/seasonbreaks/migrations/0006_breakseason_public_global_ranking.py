# Generated manually for SDA public Breaks global ranking toggle.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seasonbreaks', '0005_breakregion_public_visible'),
    ]

    operations = [
        migrations.AddField(
            model_name='breakseason',
            name='public_global_ranking',
            field=models.BooleanField(default=False,
                verbose_name='show global ranking across regions on public Breaks page'),
        ),
    ]
