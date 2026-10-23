"""Durable, manually initiated export jobs.

PostgreSQL is the queue. A renewable singleton lease serializes all preparation
and delivery, and every completion is fenced by that lease and the item token.
Network I/O never runs inside a database transaction.
"""
import logging
import threading
import uuid
from contextlib import contextmanager
from datetime import timedelta

from django.db import close_old_connections, connection, DatabaseError, transaction
from django.db.models import Count, Exists, Max, Min, OuterRef, Q
from django.utils import timezone

from adjallocation.models import DebateAdjudicator
from adjfeedback.models import AdjudicatorFeedback
from tournaments.models import Tournament

from .models import AdjudicatorStatsExportEvent, ExportJob, ExportJobItem, ExportWorkerState, FeedbackExportEvent
from .services import (
    adjudicator_stats_export_enabled, adjudicator_stats_export_endpoint,
    deliver_snapshot, feedback_export_enabled, feedback_export_endpoint, feedback_export_queryset, MAX_ATTEMPTS,
    queue_adjudicator_stats_export, queue_feedback_export, retry_delay, truncate_bytes,
)

logger = logging.getLogger(__name__)
TERMINAL = ['completed', 'completed_errors']
MODELS = {'feedback': FeedbackExportEvent, 'activity': AdjudicatorStatsExportEvent}
LEASE_SECONDS = 120
PREPARE_BATCH = 100
SEND_BATCH = 25


class LostLeaseError(Exception):
    pass


def configuration():
    state = ExportWorkerState.objects.filter(pk=1).first()
    now = timezone.now()
    return {
        'worker_online': bool(state and state.heartbeat_at and state.heartbeat_at > now - timedelta(seconds=45)),
        'heartbeat_at': state.heartbeat_at if state else None,
        'feedback_ready': feedback_export_enabled() and bool(feedback_export_endpoint()),
        'activity_ready': adjudicator_stats_export_enabled() and bool(adjudicator_stats_export_endpoint()),
    }


def create_job(*, tournament_ids, kinds, force=False, requested_by=None, submission_token=None):
    token = uuid.UUID(str(submission_token)) if submission_token else uuid.uuid4()
    existing = ExportJob.objects.filter(submission_token=token).first()
    if existing:
        return existing
    kinds = sorted(set(kinds))
    if not kinds or not set(kinds) <= set(MODELS):
        raise ValueError('Choose feedback, judge activity, or both.')
    if any(isinstance(value, bool) or not str(value).isdigit() for value in tournament_ids):
        raise ValueError('Invalid tournament selection.')
    ids = sorted(set(int(value) for value in tournament_ids))
    if any(value < 1 or value > 2147483647 for value in ids):
        raise ValueError('Invalid tournament selection.')
    if not ids:
        raise ValueError('Select at least one tournament.')
    tournaments = list(Tournament.objects.filter(id__in=ids).order_by('id').values('id', 'name', 'short_name'))
    if len(tournaments) != len(ids):
        raise ValueError('One of the selected tournaments no longer exists. Refresh the selection.')
    # These queries are bounded aggregates, not payload construction in the web request.
    limits = {}
    if 'feedback' in kinds:
        limits['feedback'] = AdjudicatorFeedback.objects.filter(
            adjudicator__tournament_id__in=ids, confirmed=True,
        ).aggregate(value=Max('id'))['value'] or 0
    if 'activity' in kinds:
        limits['activity'] = max(ids)
    job, _ = ExportJob.objects.get_or_create(submission_token=token, defaults={
        'requested_by': requested_by, 'tournaments': tournaments, 'export_types': kinds,
        'force': force, 'source_limits': limits,
    })
    return job


def create_backlog_job(*, kinds=None, requested_by=None, submission_token=None, event_ids=None):
    kinds = sorted(set(kinds or MODELS))
    if not set(kinds) <= set(MODELS):
        raise ValueError('Unknown export type.')
    limits = {kind: MODELS[kind].objects.aggregate(value=Max('id'))['value'] or 0 for kind in kinds}
    if event_ids:
        limits['event_ids'] = event_ids
    job, _ = ExportJob.objects.get_or_create(
        submission_token=uuid.UUID(str(submission_token)) if submission_token else uuid.uuid4(),
        defaults={'requested_by': requested_by, 'backlog': True, 'export_types': kinds, 'source_limits': limits},
    )
    return job


def acquire_worker():
    ExportWorkerState.objects.get_or_create(pk=1)
    with transaction.atomic():
        state = ExportWorkerState.objects.select_for_update().get(pk=1)
        now = timezone.now()
        if state.token and state.lease_expires_at and state.lease_expires_at > now:
            return None
        state.token = uuid.uuid4()
        state.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        state.heartbeat_at = now
        state.save()
        return state.token


def lock_worker(token):
    state = ExportWorkerState.objects.select_for_update().get(pk=1)
    if state.token != token or not state.lease_expires_at or state.lease_expires_at <= timezone.now():
        raise LostLeaseError()
    state.heartbeat_at = timezone.now()
    state.lease_expires_at = state.heartbeat_at + timedelta(seconds=LEASE_SECONDS)
    state.save(update_fields=['heartbeat_at', 'lease_expires_at'])
    return state


@contextmanager
def renew_lease(token, enabled):
    stop = threading.Event()

    def heartbeat():
        try:
            while not stop.wait(10):
                close_old_connections()
                now = timezone.now()
                updated = ExportWorkerState.objects.filter(pk=1, token=token, lease_expires_at__gt=now).update(
                    heartbeat_at=now, lease_expires_at=now + timedelta(seconds=LEASE_SECONDS),
                )
                if not updated:
                    return
        finally:
            close_old_connections()

    thread = threading.Thread(target=heartbeat, daemon=True) if enabled else None
    if thread:
        thread.start()
    try:
        yield
    finally:
        stop.set()
        if thread:
            thread.join(timeout=2)


def _feedback_batch(ids):
    rows = list(feedback_export_queryset().filter(id__in=ids).order_by('id'))
    debate_ids = [row.debate.id for row in rows if row.debate]
    roles = {(a.adjudicator_id, a.debate_id): a for a in DebateAdjudicator.objects.filter(debate_id__in=debate_ids)}
    tournaments = {}
    for row in rows:
        if row.debate:
            row._debateadj = roles.get((row.adjudicator_id, row.debate.id))
            tournament = row.debate.round.tournament
            if tournament.id not in tournaments:
                tournament._export_break_tournament = tournament.break_tournaments.select_related('season__league').order_by(
                    '-season__active', '-season__created_at',
                ).first()
                tournaments[tournament.id] = tournament
            row.debate.round.tournament = tournaments[tournament.id]
    return rows


def prepare_batch(job_id, token):
    # A batch and its cursor commit together. A crash cannot skip membership.
    with transaction.atomic():
        lock_worker(token)
        job = ExportJob.objects.select_for_update().get(pk=job_id)
        if job.status == 'paused' or job.preparation_done:
            return
        job.status = 'preparing'
        tournament_ids = [row['id'] for row in job.tournaments]
        remaining = PREPARE_BATCH
        for kind in job.export_types:
            cursor = job.preparation_cursor.get(kind, 0)
            limit = job.source_limits.get(kind, 0)
            if cursor >= limit or not remaining:
                continue
            if job.backlog:
                qs = MODELS[kind].objects.filter(id__gt=cursor, id__lte=limit).exclude(status='sent').order_by('id')
                selected = job.source_limits.get('event_ids', {}).get(kind)
                if selected is not None:
                    qs = qs.filter(id__in=selected)
                rows = list(qs[:remaining])
            elif kind == 'feedback':
                ids = list(AdjudicatorFeedback.objects.filter(
                    id__gt=cursor, id__lte=limit, adjudicator__tournament_id__in=tournament_ids, confirmed=True,
                ).order_by('id').values_list('id', flat=True)[:remaining])
                rows = _feedback_batch(ids)
            else:
                rows = list(Tournament.objects.filter(id__in=tournament_ids, id__gt=cursor, id__lte=limit).order_by('id')[:remaining])
            for source in rows:
                item = ExportJobItem(job=job, kind=kind, source_id=source.id)
                try:
                    if job.backlog:
                        event = source
                        item.prepared_at = event.created_at
                        item.tournament_id = event.source_tournament_id
                        item.label = '%s #%s' % (kind, event.source_feedback_id if kind == 'feedback' else event.source_tournament_id)
                        # Backlog retries retain the already prepared version, even after source deletion.
                        if not event.payload:
                            raise ValueError('No saved payload. Start a new export from the source tournament.')
                    else:
                        item.tournament_id = source.adjudicator.tournament_id if kind == 'feedback' else source.id
                        item.label = source.adjudicator.name if kind == 'feedback' else source.short_name
                        # Savepoint isolates invalid source rows from the rest of the batch.
                        with transaction.atomic():
                            event = (queue_feedback_export if kind == 'feedback' else queue_adjudicator_stats_export)(
                                source, force=job.force, reset_attempts=True,
                            )
                        if event is None:
                            raise ValueError('Feedback is no longer confirmed.')
                    setattr(item, kind + '_event', event)
                    item.status = 'unchanged' if event.status == 'sent' and not job.force else 'ready'
                    if item.status == 'unchanged':
                        item.receipt = event.receipt
                    item.save()
                except DatabaseError:
                    # Infrastructure failures must roll back the cursor, not
                    # permanently label otherwise valid source data as invalid.
                    raise
                except Exception as exc:
                    item.status = 'failed'
                    # Payload validation messages are useful, arbitrary exceptions may contain private data.
                    item.last_error = truncate_bytes(str(exc) if isinstance(exc, ValueError) else 'Could not prepare this record. Check its source data.', 2048)
                    item.save()
                    logger.warning('export_prepare_failed job=%s item=%s kind=%s', job.id, item.id, kind)
                job.preparation_cursor[kind] = source.id
            if len(rows) < remaining:
                job.preparation_cursor[kind] = limit
            remaining -= len(rows)
        job.preparation_done = all(job.preparation_cursor.get(k, 0) >= job.source_limits.get(k, 0) for k in job.export_types)
        job.last_progress_at = timezone.now()
        if job.preparation_done:
            job.status = 'running'
        job.save()


def claim_item(job_id, token):
    with transaction.atomic():
        lock_worker(token)
        job = ExportJob.objects.select_for_update().get(pk=job_id)
        if job.status == 'paused':
            return None
        now = timezone.now()
        # A former worker may have crashed between DR accepting and the local commit.
        job.items.filter(status='sending').exclude(claim_token=token).update(status='retry', next_attempt_at=now, claim_token=None)
        item = job.items.select_for_update().filter(
            status__in=['ready', 'retry'],
        ).exclude(kind__in=list(job.blocked_types)).filter(
            Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now),
        ).order_by('id').first()
        if item is None:
            return None
        if item.attempts >= MAX_ATTEMPTS:
            item.status = 'failed'
            item.last_error = 'Retry limit reached. Inspect the error and retry manually.'
            item.save()
            return item
        item.status = 'sending'
        item.claim_token = token
        item.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        item.attempts += 1
        item.save()
        job.last_progress_at = now
        job.status = 'running'
        job.save(update_fields=['last_progress_at', 'status'])
        return item


def finish_item(item_id, token, result):
    job_id = ExportJobItem.objects.values_list('job_id', flat=True).get(pk=item_id)
    with transaction.atomic():
        lock_worker(token)
        job = ExportJob.objects.select_for_update().get(pk=job_id)
        item = ExportJobItem.objects.select_for_update().get(pk=item_id)
        if item.status != 'sending' or item.claim_token != token:
            raise LostLeaseError()
        event = item.event
        status = result['status']
        item.http_status = result.get('http_status')
        item.last_error = truncate_bytes(result.get('error', ''), 2048)
        item.receipt = result.get('receipt', {})
        item.next_attempt_at = None
        if status == 'retry':
            if item.attempts >= MAX_ATTEMPTS:
                status = 'failed'
                item.last_error = truncate_bytes('Retry limit reached. ' + item.last_error, 2048)
            else:
                item.next_attempt_at = max(retry_delay(item.attempts), result.get('retry_at') or timezone.now())
        if status == 'blocked':
            # Block this stream only; the other data type can continue.
            job.blocked_types[item.kind] = item.last_error
            job.items.filter(kind=item.kind, status__in=['ready', 'retry']).update(status='blocked')
            item.attempts -= 1  # Configuration failures do not consume the retry budget.
        if item.http_status == 429 and item.next_attempt_at:
            job.items.filter(kind=item.kind, status__in=['ready', 'retry']).filter(
                Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lt=item.next_attempt_at),
            ).update(next_attempt_at=item.next_attempt_at)
        item.status = status
        item.claim_token = None
        item.lease_expires_at = None
        item.save()
        if event:
            event.attempts = item.attempts
            event.last_http_status = item.http_status
            event.last_error = item.last_error
            event.next_attempt_at = item.next_attempt_at
            event.status = {'sent': 'sent', 'failed': 'permanent_failed'}.get(status, 'failed')
            event.remote_response = result.get('diagnostic')
            if status == 'sent':
                event.sent_at = timezone.now()
                event.payload = None
                event.remote_response = None
                event.receipt = item.receipt
            event.save()
        job.last_progress_at = timezone.now()
        job.save(update_fields=['last_progress_at', 'blocked_types'])
        logger.info('export_delivery job=%s item=%s kind=%s status=%s http=%s attempt=%s',
                    job.id, item.id, item.kind, status, item.http_status, item.attempts)


def settle_job(job_id, token):
    with transaction.atomic():
        lock_worker(token)
        job = ExportJob.objects.select_for_update().get(pk=job_id)
        if job.status == 'paused' or not job.preparation_done:
            return
        counts = dict(job.items.values_list('status').annotate(n=Count('id')))
        if counts.get('ready') or counts.get('sending'):
            job.status = 'running'
        elif counts.get('retry'):
            job.status = 'waiting'
        elif counts.get('blocked'):
            job.status = 'blocked'
        else:
            job.status = 'completed_errors' if counts.get('failed') else 'completed'
            job.completed_at = timezone.now()
        job.save(update_fields=['status', 'completed_at'])


def _superseded(event, kind, prepared_at):
    source_field = 'source_feedback_id' if kind == 'feedback' else 'source_tournament_id'
    source_id = getattr(event, source_field)
    if source_id is None:
        return False
    return MODELS[kind].objects.filter(
        sent_at__gt=prepared_at, **{source_field: source_id},
    ).exclude(pk=event.pk).exists()


def worker_tick(*, heartbeat=False, should_stop=None):
    token = acquire_worker()
    if token is None:
        return False
    try:
        with renew_lease(token, heartbeat):
            job = ExportJob.objects.exclude(status__in=TERMINAL).order_by('id').first()
            if job is None or job.status == 'paused':
                return False
            if not job.preparation_done:
                prepare_batch(job.id, token)
                job.refresh_from_db()
            if job.preparation_done:
                for _ in range(SEND_BATCH):
                    if should_stop and should_stop():
                        break
                    item = claim_item(job.id, token)
                    if item is None:
                        break
                    if item.status == 'failed':
                        continue
                    event = item.event
                    if event is None:
                        result = {'status': 'failed', 'error': 'The prepared export event is missing. Start a new export.'}
                    elif _superseded(event, item.kind, item.prepared_at):
                        result = {'status': 'failed', 'error': 'A newer version was already delivered. Start a new export to send current source data.'}
                    elif event.status == 'sent' and not job.force:
                        result = {'status': 'sent', 'http_status': event.last_http_status, 'receipt': event.receipt}
                    else:
                        result = deliver_snapshot(event, item.kind)
                    finish_item(item.id, token, result)
                settle_job(job.id, token)
            return True
    except LostLeaseError:
        logger.warning('export_worker_lost_lease')
        return False
    finally:
        ExportWorkerState.objects.filter(pk=1, token=token).update(token=None, lease_expires_at=None)


def control_job(job_id, action):
    with transaction.atomic():
        job = ExportJob.objects.select_for_update().get(pk=job_id)
        if action == 'pause' and not job.terminal:
            job.status = 'paused'
        elif action == 'resume' and not job.terminal:
            job.blocked_types = {}
            job.items.filter(status='blocked').update(status='ready', next_attempt_at=None)
            job.status = 'running' if job.preparation_done else 'queued'
        elif action == 'retry' and job.terminal:
            # Retrying the same job is safe only if no later active job can use its events.
            if ExportJob.objects.filter(id__gt=job.id).exclude(status__in=TERMINAL).exists():
                raise ValueError('Finish newer jobs before retrying this export.')
            job.items.filter(status='failed').exclude(feedback_event=None, activity_event=None).update(
                status='ready', attempts=0, next_attempt_at=None, claim_token=None,
            )
            if not job.items.filter(status='ready').exists():
                raise ValueError('These records could not be prepared. Correct the source data and start a new export.')
            job.status = 'running'
            job.completed_at = None
        else:
            raise ValueError('This action is not available for the current job state.')
        job.save()
        return job


def job_summary(job):
    counts = dict(job.items.values_list('status').annotate(n=Count('id')))
    total = sum(counts.values())
    done = sum(counts.get(s, 0) for s in ['sent', 'unchanged', 'failed'])
    return {
        'id': job.id, 'status': job.status, 'status_label': job.get_status_display(),
        'terminal': job.terminal, 'preparation_done': job.preparation_done,
        'counts': counts, 'total': total, 'done': done,
        'percent': round(100 * done / total) if total and job.preparation_done else 0,
        'blocked_types': job.blocked_types, 'last_progress_at': job.last_progress_at,
        'next_attempt_at': job.items.filter(status='retry').aggregate(value=Min('next_attempt_at'))['value'],
    }


def prune_history():
    now = timezone.now()
    ExportWorkerState.objects.get_or_create(pk=1)
    with transaction.atomic():
        state = ExportWorkerState.objects.select_for_update().get(pk=1)
        if state.last_cleanup_at and state.last_cleanup_at > now - timedelta(hours=24):
            return 0
        # Completed-with-errors jobs remain available until their unresolved records are handled.
        ids = list(ExportJob.objects.filter(status='completed', completed_at__lt=now - timedelta(days=90)).values_list('id', flat=True)[:100])
        count, _ = ExportJob.objects.filter(id__in=ids).delete()
        more_receipts = False
        # Keep the latest successful receipt for each source. Older successful
        # versions may go once no retained job refers to them; failures never do.
        for kind, model in MODELS.items():
            source_field = 'source_feedback_id' if kind == 'feedback' else 'source_tournament_id'
            newer = model.objects.filter(status='sent', **{source_field: OuterRef(source_field)}).filter(
                Q(sent_at__gt=OuterRef('sent_at')) | Q(sent_at=OuterRef('sent_at'), id__gt=OuterRef('id')),
            )
            obsolete = model.objects.filter(status='sent', job_items__isnull=True).annotate(newer=Exists(newer)).filter(newer=True)
            obsolete_ids = list(obsolete.values_list('id', flat=True)[:100])
            model.objects.filter(id__in=obsolete_ids).delete()
            more_receipts = more_receipts or len(obsolete_ids) == 100
        if len(ids) < 100 and not more_receipts:
            state.last_cleanup_at = now
            state.save(update_fields=['last_cleanup_at'])
        return count


def storage_report():
    report = {}
    for kind, model in MODELS.items():
        values = {'events': model.objects.count(), 'successful_payloads': model.objects.filter(status='sent', payload__isnull=False).count()}
        if connection.vendor == 'postgresql':
            table = model._meta.db_table
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_table_size(%s), pg_indexes_size(%s)', [table, table])
                values['table_bytes'], values['index_bytes'] = cursor.fetchone()
                cursor.execute('SELECT COALESCE(SUM(pg_column_size(payload)), 0), COALESCE(SUM(pg_column_size(remote_response)), 0) FROM ' + connection.ops.quote_name(table))
                values['payload_bytes'], values['response_bytes'] = cursor.fetchone()
        report[kind] = values
    return report


def cleanup_successful(*, dry_run=False, batch_size=100):
    from .services import compact_receipt
    before = storage_report()
    cleaned = 0
    if not dry_run:
        for model in MODELS.values():
            while True:
                with transaction.atomic():
                    rows = list(model.objects.select_for_update(skip_locked=True).filter(status='sent').filter(
                        Q(payload__isnull=False) | Q(remote_response__isnull=False),
                    ).order_by('id')[:batch_size])
                    if not rows:
                        break
                    for event in rows:
                        event.receipt = event.receipt or compact_receipt(event.remote_response)
                        event.payload = None
                        event.remote_response = None
                    model.objects.bulk_update(rows, ['receipt', 'payload', 'remote_response'])
                    cleaned += len(rows)
    return {'dry_run': dry_run, 'cleaned': cleaned, 'before': before, 'after': storage_report()}
