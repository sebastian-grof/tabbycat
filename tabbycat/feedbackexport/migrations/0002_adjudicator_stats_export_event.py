from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('feedbackexport', '0001_initial'),
        ('seasonbreaks', '0003_breakseason_public_snapshot'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdjudicatorStatsExportEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'pending'), ('sent', 'sent'), ('failed', 'failed'), ('permanent_failed', 'permanently failed')], db_index=True, default='pending', max_length=20, verbose_name='status')),
                ('idempotency_key', models.CharField(max_length=160, unique=True, verbose_name='idempotency key')),
                ('attempts', models.PositiveSmallIntegerField(default=0, verbose_name='attempts')),
                ('next_attempt_at', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='next attempt at')),
                ('last_error', models.TextField(blank=True, verbose_name='last error')),
                ('last_http_status', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='last HTTP status')),
                ('payload_hash', models.CharField(blank=True, max_length=64, verbose_name='payload hash')),
                ('payload', models.JSONField(blank=True, null=True, verbose_name='payload')),
                ('remote_response', models.JSONField(blank=True, null=True, verbose_name='remote response')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='sent at')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('break_tournament', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='adjudicator_stats_export_event', to='seasonbreaks.breaktournament', verbose_name='break tournament')),
            ],
            options={
                'verbose_name': 'adjudicator stats export event',
                'verbose_name_plural': 'adjudicator stats export events',
                'ordering': ['status', '-updated_at'],
            },
        ),
    ]
