# Generated manually for SDA editable Break leagues.

import django.db.models.deletion
from django.db import migrations, models


def seed_break_leagues(apps, schema_editor):
    BreakLeague = apps.get_model('seasonbreaks', 'BreakLeague')
    BreakSeason = apps.get_model('seasonbreaks', 'BreakSeason')

    sdl, _ = BreakLeague.objects.get_or_create(slug='sdl', defaults={'name': 'SDL'})
    BreakLeague.objects.get_or_create(slug='jdl-1-kat', defaults={'name': 'JDL 1. kat'})
    jdl2, _ = BreakLeague.objects.get_or_create(slug='jdl-2-kat', defaults={'name': 'JDL 2. kat'})

    for season in BreakSeason.objects.all().iterator():
        old_league = (season.league or '').upper()
        season.league_ref = sdl if old_league == 'SDL' else jdl2
        season.save(update_fields=['league_ref'])


class Migration(migrations.Migration):

    dependencies = [
        ('seasonbreaks', '0003_breakseason_public_snapshot'),
    ]

    operations = [
        migrations.CreateModel(
            name='BreakLeague',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True, verbose_name='name')),
                ('slug', models.SlugField(max_length=80, unique=True, verbose_name='slug')),
            ],
            options={
                'verbose_name': 'break league',
                'verbose_name_plural': 'break leagues',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='breakseason',
            name='league_ref',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='seasons', to='seasonbreaks.breakleague', verbose_name='league'),
        ),
        migrations.RunPython(seed_break_leagues, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='breakseason',
            name='league',
        ),
        migrations.RenameField(
            model_name='breakseason',
            old_name='league_ref',
            new_name='league',
        ),
        migrations.AlterField(
            model_name='breakseason',
            name='league',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                related_name='seasons', to='seasonbreaks.breakleague', verbose_name='league'),
        ),
    ]
