# Generated manually for the XML converter global permission model.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import utils.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalConverterPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.CharField(choices=[('use.converter', 'use converter')], max_length=50, verbose_name='permission')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'global converter permission',
                'verbose_name_plural': 'global converter permissions',
            },
        ),
        migrations.AddConstraint(
            model_name='globalconverterpermission',
            constraint=utils.models.UniqueConstraint(fields=('user', 'permission'), name='xmlconv_globalconverterpermission_user__permission_uniq'),
        ),
    ]
