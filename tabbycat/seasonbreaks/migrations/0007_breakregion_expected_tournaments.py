# Generated manually for SDA configurable expected tournaments per region.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seasonbreaks', '0006_breakseason_public_global_ranking'),
    ]

    operations = [
        migrations.AddField(
            model_name='breakregion',
            name='expected_tournaments',
            field=models.PositiveSmallIntegerField(default=0,
                help_text='Drives the best N−1 ranking rule. Leave at 0 to use the number of '
                    'counting tournaments already added to this region.',
                verbose_name='expected tournaments this season'),
        ),
    ]
