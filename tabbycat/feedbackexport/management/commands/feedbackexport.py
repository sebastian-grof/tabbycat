import json

from django.core.management.base import BaseCommand, CommandError

from adjfeedback.models import AdjudicatorFeedback
from tournaments.models import Tournament

from feedbackexport.models import FeedbackExportEvent
from feedbackexport.services import build_feedback_payload, queue_confirmed_feedback, queue_feedback_export, send_event, send_pending_events


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

        raise CommandError('Choose one of: queue, send, retry-failed, payload')
