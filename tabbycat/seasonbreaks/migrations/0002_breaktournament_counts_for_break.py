# Generated manually for SDA Breaks tournament classification.

from django.db import migrations, models
from django.db.models import F


def exclude_trainees_from_adjudicator_totals(apps, schema_editor):
    BreakAdjudicatorTournamentStats = apps.get_model('seasonbreaks', 'BreakAdjudicatorTournamentStats')
    BreakAdjudicatorTournamentStats.objects.update(total_count=F('chair_count') + F('panellist_count'))


class Migration(migrations.Migration):

    dependencies = [
        ('seasonbreaks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='breaktournament',
            name='counts_for_break',
            field=models.BooleanField(
                default=True,
                help_text='If unchecked, this tournament only counts toward adjudicator statistics.',
                verbose_name='counts for team and speaker break',
            ),
        ),
        migrations.RunPython(exclude_trainees_from_adjudicator_totals, migrations.RunPython.noop),
    ]
