# Generated manually for SDA public Breaks region visibility.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seasonbreaks', '0004_editable_break_leagues'),
    ]

    operations = [
        migrations.AddField(
            model_name='breakregion',
            name='public_visible',
            field=models.BooleanField(default=True, verbose_name='show on public Breaks page'),
        ),
    ]
