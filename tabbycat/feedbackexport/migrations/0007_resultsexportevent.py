import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedbackexport', '0006_exportjobitem_prepared_at'),
        ('tournaments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResultsExportEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_tournament_id', models.PositiveIntegerField(blank=True, db_index=True, null=True, verbose_name='source tournament ID')),
                ('source_tournament_slug', models.SlugField(blank=True, max_length=120, verbose_name='source tournament slug')),
                ('source_tournament_name', models.CharField(blank=True, max_length=100, verbose_name='source tournament name')),
                ('source_tournament_short_name', models.CharField(blank=True, max_length=25, verbose_name='source tournament short name')),
                ('generated_at', models.DateTimeField(blank=True, null=True, verbose_name='generated at')),
                ('status', models.CharField(choices=[('pending', 'pending'), ('sent', 'sent'), ('failed', 'failed'), ('permanent_failed', 'permanently failed')], db_index=True, default='pending', max_length=20, verbose_name='status')),
                ('idempotency_key', models.CharField(max_length=160, unique=True, verbose_name='idempotency key')),
                ('attempts', models.PositiveSmallIntegerField(default=0, verbose_name='attempts')),
                ('next_attempt_at', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='next attempt at')),
                ('last_error', models.TextField(blank=True, verbose_name='last error')),
                ('last_http_status', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='last HTTP status')),
                ('receipt', models.JSONField(blank=True, default=dict)),
                ('payload_hash', models.CharField(blank=True, max_length=64, verbose_name='payload hash')),
                ('payload', models.JSONField(blank=True, null=True, verbose_name='payload')),
                ('remote_response', models.JSONField(blank=True, null=True, verbose_name='remote response')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='sent at')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('tournament', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='results_export_events', to='tournaments.tournament', verbose_name='tournament')),
            ],
            options={
                'verbose_name': 'results export event',
                'verbose_name_plural': 'results export events',
                'ordering': ['status', '-updated_at'],
            },
        ),
        migrations.AlterField(
            model_name='exportjobitem',
            name='kind',
            field=models.CharField(choices=[('feedback', 'Feedback'), ('activity', 'Judge activity'), ('results', 'Results')], max_length=16),
        ),
        migrations.AddField(
            model_name='exportjobitem',
            name='results_event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_items', to='feedbackexport.resultsexportevent'),
        ),
    ]
