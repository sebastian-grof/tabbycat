from django.db import migrations, models
import django.db.models.deletion


def populate_tournament_fields(apps, schema_editor):
    Event = apps.get_model('feedbackexport', 'AdjudicatorStatsExportEvent')
    for event in Event.objects.select_related('break_tournament__tournament').all():
        break_tournament = event.break_tournament
        if break_tournament is None:
            continue
        tournament = break_tournament.tournament
        event.tournament_id = tournament.id
        event.source_tournament_id = tournament.id
        event.source_tournament_slug = tournament.slug
        event.source_tournament_name = tournament.name
        event.source_tournament_short_name = tournament.short_name
        event.save(update_fields=[
            'tournament',
            'source_tournament_id',
            'source_tournament_slug',
            'source_tournament_name',
            'source_tournament_short_name',
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('feedbackexport', '0002_adjudicator_stats_export_event'),
        ('tournaments', '0017_tournamentcategory_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='adjudicatorstatsexportevent',
            name='tournament',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='adjudicator_stats_export_events', to='tournaments.tournament', verbose_name='tournament'),
        ),
        migrations.AddField(
            model_name='adjudicatorstatsexportevent',
            name='source_tournament_id',
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True, verbose_name='source tournament ID'),
        ),
        migrations.AddField(
            model_name='adjudicatorstatsexportevent',
            name='source_tournament_slug',
            field=models.SlugField(blank=True, max_length=120, verbose_name='source tournament slug'),
        ),
        migrations.AddField(
            model_name='adjudicatorstatsexportevent',
            name='source_tournament_name',
            field=models.CharField(blank=True, max_length=100, verbose_name='source tournament name'),
        ),
        migrations.AddField(
            model_name='adjudicatorstatsexportevent',
            name='source_tournament_short_name',
            field=models.CharField(blank=True, max_length=25, verbose_name='source tournament short name'),
        ),
        migrations.RunPython(populate_tournament_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='adjudicatorstatsexportevent',
            name='break_tournament',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='adjudicator_stats_export_event', to='seasonbreaks.breaktournament', verbose_name='break tournament'),
        ),
    ]
