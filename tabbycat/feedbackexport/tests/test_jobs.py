import io
import json
import threading
import time
import urllib.error
import uuid
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import close_old_connections, OperationalError
from django.test import Client, override_settings, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from feedbackexport.jobs import (
    acquire_worker, claim_item, cleanup_successful, control_job, create_backlog_job,
    create_job, finish_item, job_summary, LostLeaseError, prepare_batch, prune_history, worker_tick,
)
from feedbackexport.models import (
    ExportJob, ExportJobItem, ExportWorkerState, FeedbackExportEvent,
    GlobalFeedbackExportPermission,
)
from feedbackexport.services import bounded_diagnostic, queue_feedback_export

from adjfeedback.models import AdjudicatorFeedback

from . import test_feedbackexport as fixtures

EXPORT_SETTINGS = {
    'FEEDBACK_EXPORT_ENABLED': True, 'FEEDBACK_EXPORT_ENDPOINT': 'https://dr.example.test/feedback',
    'FEEDBACK_EXPORT_TOKEN': 'test-secret',
    'ADJUDICATOR_STATS_EXPORT_ENABLED': True, 'ADJUDICATOR_STATS_EXPORT_ENDPOINT': 'https://dr.example.test/activity',
}


@override_settings(**EXPORT_SETTINGS)
class ExportJobTests(TestCase):
    setUp = fixtures.FeedbackExportTestCase.setUp

    def start(self, **kwargs):
        return create_job(tournament_ids=[self.tournament.id], kinds=['feedback'], **kwargs)

    def prepare(self, job):
        token = acquire_worker()
        prepare_batch(job.id, token)
        ExportWorkerState.objects.filter(token=token).update(token=None, lease_expires_at=None)

    def due(self, job):
        job.items.filter(status='retry').update(next_attempt_at=timezone.now() - timedelta(seconds=1))

    def login_manager(self):
        user = get_user_model().objects.create_superuser(username='manager', password='pw')
        self.client.force_login(user)
        return user

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_start_returns_immediately_and_duplicate_submission_reuses_job(self, http):
        self.login_manager()
        data = {'tournament_ids': [self.tournament.id], 'export_types': ['feedback'], 'submission_token': str(uuid.uuid4())}
        started = time.monotonic()
        response = self.client.post(reverse('feedbackexport-job-create'), data=json.dumps(data), content_type='application/json')
        self.assertLess(time.monotonic() - started, 1)
        self.assertEqual(response.status_code, 202)
        duplicate = self.client.post(reverse('feedbackexport-job-create'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.json()['id'], duplicate.json()['id'])
        self.assertEqual(ExportJob.objects.count(), 1)
        self.assertEqual(ExportJobItem.objects.count(), 0)
        http.assert_not_called()

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: fixtures.FakeHTTPResponse())
    def test_one_thousand_records_finish_without_browser_requests(self, http):
        self.feedback.delete()
        AdjudicatorFeedback.objects.bulk_create([
            AdjudicatorFeedback(adjudicator=self.adjudicator, source_team=self.debate_team, score=4,
                                confirmed=True, confirm_timestamp=timezone.now(), submitter_type='p', version=version)
            for version in range(1, 1001)
        ])
        job = self.start()
        for _ in range(55):
            worker_tick()
            job.refresh_from_db()
            if job.terminal:
                break
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.items.filter(status='sent').count(), 1000)
        self.assertEqual(http.call_count, 1000)
        self.assertFalse(FeedbackExportEvent.objects.exclude(payload=None).exists())
        self.assertFalse(FeedbackExportEvent.objects.exclude(remote_response=None).exists())

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: fixtures.FakeHTTPResponse())
    def test_unchanged_skips_and_later_edit_creates_new_snapshot(self, http):
        first = self.start()
        worker_tick()
        original = first.items.get().event
        self.start()
        worker_tick()
        self.assertEqual(http.call_count, 1)
        self.assertEqual(ExportJobItem.objects.filter(status='unchanged').count(), 1)
        self.feedback.score = 2
        self.feedback.save()
        self.start()
        worker_tick()
        self.assertEqual(http.call_count, 2)
        self.assertEqual(FeedbackExportEvent.objects.count(), 2)
        original.refresh_from_db()
        self.assertIsNone(original.payload)

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: fixtures.FakeHTTPResponse())
    def test_reverting_content_compares_with_latest_receipt(self, http):
        original_score = self.feedback.score
        self.start()
        worker_tick()
        original_key = http.call_args.args[0].headers['Idempotency-key']
        self.feedback.score = 2
        self.feedback.save()
        self.start()
        worker_tick()
        self.feedback.score = original_score
        self.feedback.save()
        reverted = self.start()
        worker_tick()
        self.assertEqual(http.call_count, 3)
        self.assertEqual(http.call_args.args[0].headers['Idempotency-key'], original_key)
        self.assertEqual(reverted.items.get().status, 'sent')
        self.start()
        worker_tick()
        self.assertEqual(http.call_count, 3)

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_old_failed_snapshot_is_preserved_but_cannot_overwrite_newer_success(self, http):
        http.side_effect = urllib.error.HTTPError('https://dr.example.test', 422, '', {}, io.BytesIO(b'{}'))
        old_job = self.start()
        worker_tick()
        old_event = old_job.items.get().event
        original_payload = old_event.payload
        self.feedback.score = 2
        self.feedback.save()
        self.start()
        http.side_effect = lambda *a, **k: fixtures.FakeHTTPResponse()
        worker_tick()
        old_event.refresh_from_db()
        self.assertEqual(old_event.payload, original_payload)
        control_job(old_job.id, 'retry')
        worker_tick()
        self.assertEqual(http.call_count, 2)
        self.assertEqual(old_job.items.get().status, 'failed')
        self.assertIn('newer version', old_job.items.get().last_error)
        backlog = create_backlog_job()
        worker_tick()
        self.assertEqual(backlog.items.get().status, 'failed')
        self.assertEqual(http.call_count, 2)

    @patch('feedbackexport.jobs.queue_feedback_export', side_effect=OperationalError('database unavailable'))
    def test_database_failure_rolls_back_preparation_cursor(self, prepare):
        job = self.start()
        with self.assertRaises(OperationalError):
            worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.preparation_cursor, {})
        self.assertFalse(job.items.exists())

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_retry_preserves_exact_payload_and_key_after_source_edit(self, http):
        job = self.start()
        http.side_effect = urllib.error.URLError('connection lost')
        worker_tick()
        first_request = http.call_args.args[0]
        self.feedback.score = 1
        self.feedback.save()
        self.due(job)
        http.side_effect = None
        http.return_value = fixtures.FakeHTTPResponse()
        worker_tick()
        second_request = http.call_args.args[0]
        self.assertEqual(first_request.data, second_request.data)
        self.assertEqual(first_request.headers['Idempotency-key'], second_request.headers['Idempotency-key'])
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')

    def test_real_http_transport_retries_lost_acknowledgement_identically(self):
        requests = []

        class Receiver(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler interface
                requests.append((self.headers['Idempotency-Key'], self.rfile.read(int(self.headers['Content-Length']))))
                if len(requests) == 1:
                    # Simulate DR accepting the body then losing its response.
                    self.close_connection = True
                    return
                self.send_response(201)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"id":"local-receipt","message":"Accepted"}')

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Receiver)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with override_settings(FEEDBACK_EXPORT_ENDPOINT='http://127.0.0.1:%s/feedback' % server.server_port):
                job = self.start()
                worker_tick()
                self.assertEqual(job.items.get().status, 'retry')
                self.due(job)
                worker_tick()
                self.assertEqual(job.items.get().status, 'sent')
                self.assertEqual(job.items.get().receipt['id'], 'local-receipt')
                self.assertEqual(len(requests), 2)
                self.assertEqual(requests[0], requests[1])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_rate_limit_honors_retry_after_and_does_not_sleep_in_worker(self, http):
        http.side_effect = urllib.error.HTTPError('https://dr.example.test', 429, '', {'Retry-After': '600'}, io.BytesIO(b'{}'))
        job = self.start()
        worker_tick()
        item = job.items.get()
        self.assertEqual(item.status, 'retry')
        self.assertGreater(item.next_attempt_at, timezone.now() + timedelta(minutes=9))
        worker_tick()
        self.assertEqual(http.call_count, 1)
        self.due(job)
        http.side_effect = None
        http.return_value = fixtures.FakeHTTPResponse()
        worker_tick()
        self.assertEqual(http.call_count, 2)

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_authentication_blocks_only_affected_stream(self, http):
        def response(request, **kwargs):
            if '/feedback' in request.full_url:
                raise urllib.error.HTTPError(request.full_url, 401, '', {}, io.BytesIO(b'{"detail":"bad token"}'))
            return fixtures.FakeHTTPResponse()
        http.side_effect = response
        job = create_job(tournament_ids=[self.tournament.id], kinds=['feedback', 'activity'])
        worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.status, 'blocked')
        self.assertEqual(job.items.get(kind='activity').status, 'sent')
        self.assertEqual(job.items.get(kind='feedback').attempts, 0)
        worker_tick()
        self.assertEqual(http.call_count, 2)
        control_job(job.id, 'resume')
        http.side_effect = lambda *a, **k: fixtures.FakeHTTPResponse()
        worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')

    @override_settings(FEEDBACK_EXPORT_ENABLED=False)
    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_disabled_send_flag_is_enforced_in_worker(self, http):
        job = self.start()
        worker_tick()
        self.assertEqual(job.items.get().status, 'blocked')
        http.assert_not_called()

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_409_is_terminal_not_an_unbounded_retry(self, http):
        http.side_effect = urllib.error.HTTPError('https://dr.example.test', 409, '', {}, io.BytesIO(b'{}'))
        job = self.start()
        worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed_errors')
        self.assertIn('conflict', job.items.get().last_error)
        worker_tick()
        self.assertEqual(http.call_count, 1)

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=urllib.error.URLError('timeout'))
    def test_retry_exhaustion_is_visible_and_can_be_retried(self, http):
        job = self.start()
        for _ in range(8):
            worker_tick()
            self.due(job)
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed_errors')
        self.assertEqual(job.items.get().attempts, 8)
        control_job(job.id, 'retry')
        self.assertEqual(job.items.get().attempts, 0)
        worker_tick()
        self.assertEqual(http.call_count, 9)

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: fixtures.FakeHTTPResponse())
    def test_invalid_record_does_not_abort_preparation(self, http):
        other = AdjudicatorFeedback.objects.create(adjudicator=self.adjudicator, source_adjudicator=self.source_debate_adjudicator,
                                                  score=3, confirmed=True, submitter_type='p')
        self.source_adjudicator.name = ''
        self.source_adjudicator.save()
        job = self.start()
        worker_tick()
        self.assertEqual(job.items.get(source_id=self.feedback.id).status, 'sent')
        self.assertEqual(job.items.get(source_id=other.id).status, 'failed')
        self.assertEqual(http.call_count, 1)

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: fixtures.FakeHTTPResponse())
    def test_prepared_feedback_survives_source_deletion(self, http):
        job = self.start()
        self.prepare(job)
        event = job.items.get().event
        payload = event.payload
        self.feedback.delete()
        event.refresh_from_db()
        self.assertIsNone(event.feedback)
        self.assertIsNotNone(event.source_feedback_id)
        worker_tick()
        self.assertEqual(json.loads(http.call_args.args[0].data), payload)
        self.assertEqual(job.items.get().status, 'sent')

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: fixtures.FakeHTTPResponse())
    def test_backlog_requires_explicit_start_and_preserves_deleted_source(self, http):
        event = queue_feedback_export(self.feedback)
        payload = event.payload
        self.feedback.delete()
        worker_tick()
        http.assert_not_called()
        job = create_backlog_job()
        worker_tick()
        self.assertEqual(job.items.get().status, 'sent')
        self.assertEqual(json.loads(http.call_args.args[0].data), payload)

    def test_expired_claim_is_recovered_and_old_result_is_fenced(self):
        job = self.start()
        first = acquire_worker()
        prepare_batch(job.id, first)
        item = claim_item(job.id, first)
        ExportWorkerState.objects.filter(pk=1).update(lease_expires_at=timezone.now() - timedelta(seconds=1))
        second = acquire_worker()
        recovered = claim_item(job.id, second)
        self.assertEqual(item.id, recovered.id)
        with self.assertRaises(LostLeaseError):
            finish_item(item.id, first, {'status': 'failed', 'error': 'stale'})
        finish_item(item.id, second, {'status': 'sent', 'http_status': 201, 'receipt': {'id': 'ok'}})
        self.assertEqual(job.items.get().status, 'sent')

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_pause_survives_restart_and_blocks_later_jobs(self, http):
        first = self.start()
        control_job(first.id, 'pause')
        second = self.start()
        worker_tick()
        http.assert_not_called()
        self.assertFalse(second.items.exists())
        control_job(first.id, 'resume')
        http.return_value = fixtures.FakeHTTPResponse()
        worker_tick()
        self.assertEqual(first.items.get().status, 'sent')

    def test_cleanup_preserves_hashes_and_unresolved_payloads(self):
        event = queue_feedback_export(self.feedback)
        original = event.payload
        original_hash = event.payload_hash
        FeedbackExportEvent.objects.filter(pk=event.pk).update(status='sent', remote_response={'id': 'DR-1'})
        self.feedback.score = 1
        self.feedback.save()
        failed = queue_feedback_export(self.feedback)
        result = cleanup_successful(dry_run=True)
        self.assertEqual(result['cleaned'], 0)
        event.refresh_from_db()
        self.assertEqual(event.payload, original)
        self.assertEqual(cleanup_successful(batch_size=1)['cleaned'], 1)
        event.refresh_from_db()
        failed.refresh_from_db()
        self.assertIsNone(event.payload)
        self.assertIsNone(event.remote_response)
        self.assertEqual(event.payload_hash, original_hash)
        self.assertEqual(event.receipt['id'], 'DR-1')
        self.assertIsNotNone(failed.payload)
        self.assertEqual(cleanup_successful()['cleaned'], 0)

    def test_cleanup_retains_unresolved_jobs_and_latest_receipt(self):
        successful = self.start()
        self.prepare(successful)
        event = successful.items.get().event
        event.mark_sent({'id': 'DR-1'}, 201)
        successful.status = 'completed'
        successful.completed_at = timezone.now() - timedelta(days=91)
        successful.save()
        unresolved = self.start()
        unresolved.status = 'completed_errors'
        unresolved.completed_at = timezone.now() - timedelta(days=91)
        unresolved.save()
        prune_history()
        self.assertFalse(ExportJob.objects.filter(pk=successful.id).exists())
        self.assertTrue(ExportJob.objects.filter(pk=unresolved.id).exists())
        self.assertTrue(FeedbackExportEvent.objects.filter(pk=event.id).exists())

    def test_json_diagnostics_are_byte_bounded(self):
        value = bounded_diagnostic({'detail': '\\"' * 20000 + 'ž' * 20000})
        self.assertLessEqual(len(json.dumps(value, ensure_ascii=False).encode('utf-8')), 4096)

    def test_status_and_history_do_not_rebuild_payloads_or_expose_tokens(self):
        self.login_manager()
        job = self.start()
        self.prepare(job)
        with patch('feedbackexport.services.build_feedback_payload', side_effect=AssertionError('No rebuild')):
            for name in ['feedbackexport-index', 'feedbackexport-history', 'feedbackexport-access']:
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
            for name in ['feedbackexport-job', 'feedbackexport-job-status', 'feedbackexport-job-items']:
                response = self.client.get(reverse(name, args=[job.id]))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'test-secret')
                self.assertNotContains(response, 'dr.example.test')
        summary = job_summary(job)
        self.assertEqual(summary['total'], 1)
        self.assertNotIn('payload', summary)

    def test_view_permissions_and_csrf_are_enforced(self):
        job = self.start()
        user = get_user_model().objects.create_user('viewer', password='pw')
        GlobalFeedbackExportPermission.objects.create(user=user, permission='view.feedback_export')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('feedbackexport-job-status', args=[job.id])).status_code, 200)
        self.assertEqual(self.client.post(reverse('feedbackexport-job-create')).status_code, 403)
        self.assertEqual(self.client.post(reverse('feedbackexport-job-control', args=[job.id, 'pause'])).status_code, 403)
        user.is_superuser = True
        user.save()
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        self.assertEqual(client.post(reverse('feedbackexport-job-control', args=[job.id, 'pause'])).status_code, 403)

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_legacy_cli_only_enqueues(self, http):
        output = io.StringIO()
        call_command('feedbackexport', 'queue', '--tournament', self.tournament.slug, stdout=output)
        self.assertIn('job_id', output.getvalue())
        self.assertEqual(ExportJob.objects.count(), 1)
        http.assert_not_called()


@override_settings(**EXPORT_SETTINGS)
class ConcurrentExportTests(TransactionTestCase):
    setUp = fixtures.FeedbackExportTestCase.setUp

    def test_second_worker_cannot_send_and_pause_allows_inflight_completion(self):
        job = create_job(tournament_ids=[self.tournament.id], kinds=['feedback'])
        entered = threading.Event()
        release = threading.Event()
        failures = []

        def response(*args, **kwargs):
            entered.set()
            release.wait(10)
            return fixtures.FakeHTTPResponse()

        def run():
            close_old_connections()
            try:
                worker_tick()
            except Exception as exc:
                failures.append(exc)
            finally:
                close_old_connections()

        with patch('feedbackexport.services.urllib.request.urlopen', side_effect=response) as http:
            thread = threading.Thread(target=run)
            thread.start()
            try:
                self.assertTrue(entered.wait(10))
                self.assertFalse(worker_tick())
                control_job(job.id, 'pause')
            finally:
                release.set()
                thread.join(10)
            self.assertFalse(thread.is_alive())
            self.assertFalse(failures)
            self.assertEqual(http.call_count, 1)
        job.refresh_from_db()
        self.assertEqual(job.status, 'paused')
        self.assertEqual(job.items.get().status, 'sent')
        control_job(job.id, 'resume')
        worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')


class ExportMigrationTests(TransactionTestCase):
    setUp = fixtures.FeedbackExportTestCase.setUp

    def test_upgrade_preserves_backlog_payload_key_and_source_identifiers(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        previous = [('feedbackexport', '0004_remove_tabbycat_judge_mapping')]
        current = [('feedbackexport', '0006_exportjobitem_prepared_at')]
        executor = MigrationExecutor(connection)
        try:
            executor.migrate(previous)
            apps = executor.loader.project_state(previous).apps
            legacy = apps.get_model('feedbackexport', 'FeedbackExportEvent').objects.create(
                feedback_id=self.feedback.id, idempotency_key='legacy-key', payload={'saved': True},
                payload_hash='a' * 64, status='pending', attempts=3,
            )
            MigrationExecutor(connection).migrate(current)
            event = FeedbackExportEvent.objects.get(pk=legacy.id)
            self.assertEqual(event.source_feedback_id, self.feedback.id)
            self.assertEqual(event.source_tournament_id, self.tournament.id)
            self.assertEqual(event.idempotency_key, 'legacy-key')
            self.assertEqual(event.payload, {'saved': True})
            self.assertEqual(event.attempts, 3)
            self.assertFalse(ExportJob.objects.exists())
        finally:
            MigrationExecutor(connection).migrate(current)
