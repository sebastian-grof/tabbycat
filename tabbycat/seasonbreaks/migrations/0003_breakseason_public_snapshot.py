# Generated manually for SDA public Breaks snapshots.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seasonbreaks', '0002_breaktournament_counts_for_break'),
    ]

    operations = [
        migrations.AddField(
            model_name='breakseason',
            name='public',
            field=models.BooleanField(default=False, verbose_name='show on public Breaks page'),
        ),
        migrations.AddField(
            model_name='breakseason',
            name='public_published_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='public snapshot published at'),
        ),
        migrations.AddField(
            model_name='breakseason',
            name='public_snapshot',
            field=models.JSONField(blank=True, null=True, verbose_name='public snapshot'),
        ),
    ]
