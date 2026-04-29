# Generated manually for the XML converter access management permission.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xmlconverter', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalconverterpermission',
            name='permission',
            field=models.CharField(
                choices=[
                    ('use.converter', 'use converter'),
                    ('manage.converter_access', 'manage converter access'),
                ],
                max_length=50,
                verbose_name='permission',
            ),
        ),
    ]
