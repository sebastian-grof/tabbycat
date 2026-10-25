import json
import signal
import threading

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from feedbackexport.jobs import (
    cleanup_successful, configuration, create_backlog_job, create_job, prune_history, worker_tick,
)
from feedbackexport.services import build_adjudicator_stats_payload, build_feedback_payload
from tournaments.models import Tournament


class Command(BaseCommand):
    help = 'Start manual DR export jobs, run the durable worker, or compact successful receipts.'

    def add_arguments(self, parser):
        commands = parser.add_subparsers(dest='command', required=True)
        worker = commands.add_parser('worker')
        worker.add_argument('--once', action='store_true', help='Process one preparation/delivery batch and exit')
        worker.add_argument('--poll-interval', type=float, default=2)
        commands.add_parser('healthcheck')
        cleanup = commands.add_parser('cleanup')
        cleanup.add_argument('--dry-run', action='store_true')
        cleanup.add_argument('--batch-size', type=int, default=100)
        for name in ('queue', 'queue-adjudicator-stats'):
            command = commands.add_parser(name)
            command.add_argument('--tournament', help='Tournament slug; omission selects all tournaments')
            command.add_argument('--force', action='store_true')
            command.add_argument('--reset-attempts', action='store_true', help='Compatibility flag; new jobs start a fresh retry budget')
            if name == 'queue-adjudicator-stats':
                command.add_argument('--season')
                command.add_argument('--break-tournament', type=int)
        for name in ('send', 'send-adjudicator-stats', 'retry-failed', 'retry-failed-adjudicator-stats'):
            command = commands.add_parser(name)
            command.add_argument('--dry-run', action='store_true')
            command.add_argument('--limit', type=int, default=50, help='Compatibility option; background jobs drain the complete backlog')
            command.add_argument('--reset-attempts', action='store_true')
        for name, argument in [('payload', 'feedback_id'), ('adjudicator-stats-payload', 'tournament_id')]:
            commands.add_parser(name).add_argument(argument, type=int)

    def handle(self, *args, **options):
        command = options['command']
        if command == 'worker':
            if options['poll_interval'] <= 0:
                raise CommandError('Poll interval must be positive.')
            stop = threading.Event()
            previous = {}
            if threading.current_thread() is threading.main_thread():
                for sig in (signal.SIGTERM, signal.SIGINT):
                    previous[sig] = signal.getsignal(sig)
                    signal.signal(sig, lambda *_: stop.set())
            try:
                while not stop.is_set():
                    close_old_connections()
                    worker_tick(heartbeat=True, should_stop=stop.is_set)
                    prune_history()
                    if options['once']:
                        break
                    stop.wait(options['poll_interval'])
            finally:
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
            return
        if command == 'healthcheck':
            health = configuration()
            if not health['worker_online']:
                raise CommandError('DR export worker heartbeat is stale or missing.')
            self.stdout.write('DR export worker is online.')
            return
        if command == 'cleanup':
            if options['batch_size'] < 1:
                raise CommandError('Batch size must be positive.')
            result = cleanup_successful(dry_run=options['dry_run'], batch_size=options['batch_size'])
        elif command == 'payload':
            result = build_feedback_payload(options['feedback_id'])
        elif command == 'adjudicator-stats-payload':
            result = build_adjudicator_stats_payload(options['tournament_id'])
        else:
            kind = 'activity' if 'adjudicator-stats' in command else 'feedback'
            if command.startswith('queue'):
                tournaments = Tournament.objects.all()
                if options.get('tournament'):
                    tournaments = tournaments.filter(slug=options['tournament'])
                if options.get('season'):
                    tournaments = tournaments.filter(break_tournaments__season__slug=options['season'])
                if options.get('break_tournament'):
                    tournaments = tournaments.filter(break_tournaments__id=options['break_tournament'])
                try:
                    job = create_job(tournament_ids=list(tournaments.values_list('id', flat=True).distinct()), kinds=[kind], force=options['force'])
                except ValueError as exc:
                    raise CommandError(str(exc)) from exc
            elif options['dry_run']:
                from feedbackexport.jobs import MODELS
                result = {'pending': MODELS[kind].objects.exclude(status='sent').count(), 'dry_run': True}
                self.stdout.write(json.dumps(result))
                return
            else:
                job = create_backlog_job(kinds=[kind])
            result = {'job_id': job.id, 'status': job.status, 'message': 'Job saved. The export worker will process it.'}
        self.stdout.write(json.dumps(result, indent=2, sort_keys=True, default=str))
