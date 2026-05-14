import json

from django.core.management.base import BaseCommand, CommandError

from adjfeedback.models import AdjudicatorFeedback
from seasonbreaks.models import BreakSeason, BreakTournament
from tournaments.models import Tournament

from feedbackexport.models import AdjudicatorStatsExportEvent, FeedbackExportEvent
from feedbackexport.services import (
    build_adjudicator_stats_payload,
    build_feedback_payload,
    queue_adjudicator_stats_export,
    queue_confirmed_feedback,
    queue_feedback_export,
    send_pending_adjudicator_stats_events,
    send_pending_events,
)


class Command(BaseCommand):
    help = 'Queue, send and inspect adjudicator feedback export events.'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='command')

        queue = subparsers.add_parser('queue')
        queue.add_argument('--tournament', help='Only queue confirmed feedback from this tournament slug')
        queue.add_argument('--force', action='store_true', help='Rebuild events even if they were already sent')
        queue.add_argument('--reset-attempts', action='store_true', help='Reset attempts while queueing')

        send = subparsers.add_parser('send')
        send.add_argument('--limit', type=int, default=50)
        send.add_argument('--dry-run', action='store_true')

        retry = subparsers.add_parser('retry-failed')
        retry.add_argument('--reset-attempts', action='store_true', default=True)

        payload = subparsers.add_parser('payload')
        payload.add_argument('feedback_id', type=int)

        stats_queue = subparsers.add_parser('queue-adjudicator-stats')
        stats_queue.add_argument('--season', help='Only queue stats from this break season slug')
        stats_queue.add_argument('--break-tournament', type=int, help='Only queue this BreakTournament ID')
        stats_queue.add_argument('--force', action='store_true', help='Rebuild events even if they were already sent')
        stats_queue.add_argument('--reset-attempts', action='store_true', help='Reset attempts while queueing')

        stats_send = subparsers.add_parser('send-adjudicator-stats')
        stats_send.add_argument('--limit', type=int, default=50)
        stats_send.add_argument('--dry-run', action='store_true')

        stats_retry = subparsers.add_parser('retry-failed-adjudicator-stats')
        stats_retry.add_argument('--reset-attempts', action='store_true', default=True)

        stats_payload = subparsers.add_parser('adjudicator-stats-payload')
        stats_payload.add_argument('break_tournament_id', type=int)

    def handle(self, *args, **options):
        command = options.get('command')
        if command == 'queue':
            queryset = AdjudicatorFeedback.objects.filter(confirmed=True)
            if options.get('tournament'):
                try:
                    tournament = Tournament.objects.get(slug=options['tournament'])
                except Tournament.DoesNotExist as exc:
                    raise CommandError('Tournament not found: %s' % options['tournament']) from exc
                queryset = queryset.filter(adjudicator__tournament=tournament)
            result = queue_confirmed_feedback(
                queryset=queryset,
                force=options.get('force', False),
                reset_attempts=options.get('reset_attempts', False),
            )
            self.stdout.write(self.style.SUCCESS(json.dumps(result, sort_keys=True)))
            return

        if command == 'send':
            result = send_pending_events(limit=options['limit'], dry_run=options['dry_run'])
            self.stdout.write(self.style.SUCCESS(json.dumps(result, sort_keys=True)))
            return

        if command == 'retry-failed':
            count = 0
            for event in FeedbackExportEvent.objects.filter(
                status__in=[FeedbackExportEvent.Status.FAILED, FeedbackExportEvent.Status.PERMANENT_FAILED]
            ).select_related('feedback'):
                queue_feedback_export(event.feedback, force=True, reset_attempts=options['reset_attempts'])
                count += 1
            self.stdout.write(self.style.SUCCESS(json.dumps({'queued': count}, sort_keys=True)))
            return

        if command == 'payload':
            payload = build_feedback_payload(options['feedback_id'])
            self.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
            return

        if command == 'queue-adjudicator-stats':
            queryset = BreakTournament.objects.select_related('season', 'tournament').exclude(frozen_at__isnull=True)
            if options.get('season'):
                try:
                    season = BreakSeason.objects.get(slug=options['season'])
                except BreakSeason.DoesNotExist as exc:
                    raise CommandError('Break season not found: %s' % options['season']) from exc
                queryset = queryset.filter(season=season)
            if options.get('break_tournament'):
                queryset = queryset.filter(id=options['break_tournament'])
            count = 0
            for break_tournament in queryset.iterator():
                queue_adjudicator_stats_export(
                    break_tournament,
                    force=options.get('force', False),
                    reset_attempts=options.get('reset_attempts', False),
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(json.dumps({'queued': count}, sort_keys=True)))
            return

        if command == 'send-adjudicator-stats':
            result = send_pending_adjudicator_stats_events(limit=options['limit'], dry_run=options['dry_run'])
            self.stdout.write(self.style.SUCCESS(json.dumps(result, sort_keys=True)))
            return

        if command == 'retry-failed-adjudicator-stats':
            count = 0
            for event in AdjudicatorStatsExportEvent.objects.filter(
                status__in=[
                    AdjudicatorStatsExportEvent.Status.FAILED,
                    AdjudicatorStatsExportEvent.Status.PERMANENT_FAILED,
                ]
            ).select_related('break_tournament'):
                queue_adjudicator_stats_export(
                    event.break_tournament,
                    force=True,
                    reset_attempts=options['reset_attempts'],
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(json.dumps({'queued': count}, sort_keys=True)))
            return

        if command == 'adjudicator-stats-payload':
            payload = build_adjudicator_stats_payload(options['break_tournament_id'])
            self.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
            return

        raise CommandError('Choose one of: queue, send, retry-failed, payload, queue-adjudicator-stats, send-adjudicator-stats, retry-failed-adjudicator-stats, adjudicator-stats-payload')
