"""Season breaks export (POST /api/v1/season-breaks/, payload v1).

Publishing a break season's public snapshot queues one export job; the export
worker sends the snapshot exactly as published, keyed by season and publication
time. Databáza SDA stores it as sent and never recomputes the rankings.
"""
import io
import json
import os
import runpy
import urllib.error
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils.translation import gettext as _

from feedbackexport.jobs import (
    configuration, control_job, create_job, create_season_breaks_job, season_breaks_export_status, worker_tick,
)
from feedbackexport.models import ExportJob, SeasonBreaksExportEvent
from feedbackexport.services import (
    build_season_breaks_payload, make_season_breaks_idempotency_key, queue_season_breaks_export,
    validate_season_breaks_payload,
)
from seasonbreaks.models import (
    BreakLeague, BreakRegion, BreakSeason, BreakSpeaker, BreakSpeakerTournamentParticipation, BreaksPermission,
    BreakTeam, BreakTeamTournamentResult, BreakTournament, GlobalBreaksPermission,
)
from seasonbreaks.services import publish_public_breaks_snapshot
from tournaments.models import Tournament

from .test_feedbackexport import FakeHTTPResponse

ENDPOINT = 'https://dr.example.test/api/v1/season-breaks/'
BREAKS_SETTINGS = {
    'SEASON_BREAKS_EXPORT_ENABLED': True, 'SEASON_BREAKS_EXPORT_ENDPOINT': ENDPOINT,
    'SEASON_BREAKS_EXPORT_TOKEN': 'results-secret',
}
DISABLED_SETTINGS = {**BREAKS_SETTINGS, 'SEASON_BREAKS_EXPORT_ENABLED': False}


def ok_response(*args, **kwargs):
    return FakeHTTPResponse(status=201, body=b'{"status": "imported", "id": 7}')


class SeasonBreaksFixtureMixin:
    """A league season with two regions and one ranked team in each."""

    def setUp(self):
        league = BreakLeague.objects.get_or_create(slug='sdl', defaults={'name': 'SDL'})[0]
        self.season = BreakSeason.objects.create(
            name='SDL 2026/2027', slug='sdl-2026-2027', league=league, regional_slots=2,
        )
        west = BreakRegion.objects.create(season=self.season, name='West', seq=1)
        east = BreakRegion.objects.create(season=self.season, name='East', seq=2)
        for region, short in ((west, 'W1'), (east, 'E1')):
            tournament = Tournament.objects.create(name=region.name + ' Open', short_name=short, slug=short.lower())
            break_tournament = BreakTournament.objects.create(
                season=self.season, tournament=tournament, region=region, seq=region.seq,
            )
            team = BreakTeam.objects.create(season=self.season, name=region.name + ' A', region=region)
            for index in range(2):
                speaker = BreakSpeaker.objects.create(season=self.season, name='%s speaker %d' % (region.name, index))
                BreakSpeakerTournamentParticipation.objects.create(
                    break_tournament=break_tournament, break_speaker=speaker, break_team=team, speeches=2, rounds=2,
                )
            BreakTeamTournamentResult.objects.create(
                break_tournament=break_tournament, break_team=team, wins=2, ballots=6, speaker_score=600,
                rounds_debated=3, majority_debated=True,
            )

    def publish(self, **kwargs):
        snapshot = publish_public_breaks_snapshot(self.season, **kwargs)
        self.season.refresh_from_db()
        return snapshot

    def sent_requests(self, http):
        return [call.args[0] for call in http.call_args_list]


@override_settings(**DISABLED_SETTINGS)
class SeasonBreaksPayloadTests(SeasonBreaksFixtureMixin, TestCase):

    def test_payload_wraps_the_published_snapshot_unchanged(self):
        snapshot = self.publish()
        payload = build_season_breaks_payload(self.season)
        self.assertEqual(set(payload), {'version', 'source_system', 'generated_at', 'season', 'snapshot'})
        self.assertEqual(payload['version'], 1)
        self.assertEqual(payload['source_system'], 'tabbycat-sda')
        self.assertIsInstance(datetime.fromisoformat(payload['generated_at']), datetime)
        self.assertEqual(payload['season'], '2026/2027')
        self.assertEqual(payload['snapshot'], snapshot)
        self.assertEqual(payload['snapshot'], self.season.public_snapshot)
        self.assertEqual([r['name'] for r in payload['snapshot']['regions']], ['West', 'East'])
        self.assertEqual(validate_season_breaks_payload(payload), payload)

    def test_payload_is_not_recomputed_from_live_data(self):
        snapshot = self.publish()
        BreakTeamTournamentResult.objects.update(wins=99)
        self.assertEqual(build_season_breaks_payload(self.season)['snapshot'], snapshot)

    def test_sda_season_is_omitted_when_the_season_names_none(self):
        self.season.name, self.season.slug = 'SDL Autumn', 'sdl-autumn'
        self.season.save()
        self.publish()
        self.assertNotIn('season', build_season_breaks_payload(self.season))

    def test_sda_season_comes_from_the_snapshot_not_a_later_rename(self):
        self.publish()
        self.season.name = 'SDL 2030/2031'
        self.season.save()
        self.assertEqual(build_season_breaks_payload(self.season)['season'], '2026/2027')

    def test_unpublished_season_has_no_payload(self):
        with self.assertRaisesMessage(ValueError, 'no published snapshot'):
            build_season_breaks_payload(self.season)

    def test_idempotency_key_names_season_and_publication_time(self):
        snapshot = self.publish()
        event = queue_season_breaks_export(self.season)
        self.assertEqual(event.idempotency_key, 'tabbycat-sda:season-breaks:%d:%s' % (
            self.season.id, snapshot['published_at']))
        self.assertEqual(event.idempotency_key, make_season_breaks_idempotency_key(
            self.season.id, self.season.public_published_at.isoformat()))
        self.assertEqual(event.published_at, self.season.public_published_at)
        self.assertEqual((event.source_season_id, event.source_season_slug), (self.season.id, self.season.slug))
        # The key travels as a header, not in the body.
        self.assertNotIn('idempotency_key', event.payload)

    def test_requeueing_the_same_snapshot_keeps_key_and_body(self):
        self.publish()
        first = queue_season_breaks_export(self.season)
        body = json.dumps(first.payload, sort_keys=True)
        second = queue_season_breaks_export(self.season, force=True)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(json.dumps(second.payload, sort_keys=True), body)

    def test_validation_rejects_unknown_snapshot_versions(self):
        self.publish()
        payload = build_season_breaks_payload(self.season)
        payload['snapshot'] = {**payload['snapshot'], 'version': 2}
        with self.assertRaisesMessage(ValueError, 'Unsupported break snapshot version'):
            validate_season_breaks_payload(payload)

    def test_payload_command_prints_payload(self):
        self.publish()
        out = io.StringIO()
        call_command('feedbackexport', 'season-breaks-payload', str(self.season.id), stdout=out)
        self.assertEqual(json.loads(out.getvalue())['snapshot']['season']['id'], self.season.id)


@override_settings(**BREAKS_SETTINGS)
class SeasonBreaksPublishHookTests(SeasonBreaksFixtureMixin, TestCase):

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=ok_response)
    def test_publishing_queues_one_job_and_the_worker_sends_the_snapshot(self, http):
        user = get_user_model().objects.create_user(username='breaks-admin')
        snapshot = self.publish(requested_by=user)
        http.assert_not_called()  # Publishing only saves a job.
        job = ExportJob.objects.get()
        self.assertEqual((job.export_types, job.seasons, job.requested_by), (
            ['breaks'], [{'id': self.season.id, 'name': self.season.name, 'slug': self.season.slug}], user))

        worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        request = http.call_args.args[0]
        self.assertEqual(request.full_url, ENDPOINT)
        self.assertEqual(request.get_method(), 'POST')
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(headers['authorization'], 'Bearer results-secret')
        self.assertEqual(headers['content-type'], 'application/json')
        self.assertEqual(headers['idempotency-key'], 'tabbycat-sda:season-breaks:%d:%s' % (
            self.season.id, snapshot['published_at']))
        self.assertNotIn('content-encoding', headers)
        body = json.loads(request.data)
        self.assertEqual(body['snapshot'], snapshot)
        self.assertEqual(body['season'], '2026/2027')

        event = SeasonBreaksExportEvent.objects.get()
        self.assertEqual((event.status, event.last_http_status, event.season), ('sent', 201, self.season))
        self.assertEqual(event.receipt, {'summary': 'imported', 'id': '7'})
        self.assertIsNone(event.payload)
        item = job.items.get()
        self.assertEqual((item.kind, item.label, item.tournament_id), ('breaks', self.season.name, None))

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=ok_response)
    def test_republishing_sends_the_new_snapshot_under_a_new_key(self, http):
        self.publish()
        worker_tick()
        self.publish()
        worker_tick()
        keys = [dict(r.header_items())['Idempotency-key'] for r in self.sent_requests(http)]
        self.assertEqual(len(set(keys)), 2)
        self.assertTrue(keys[1].endswith(self.season.public_snapshot['published_at']))
        self.assertEqual(SeasonBreaksExportEvent.objects.filter(status='sent').count(), 2)

    @override_settings(**DISABLED_SETTINGS)
    def test_disabled_stream_publishes_without_queueing(self):
        self.publish()
        self.assertIsNotNone(self.season.public_snapshot)
        self.assertFalse(ExportJob.objects.exists())
        self.assertFalse(configuration()['breaks_ready'])

    @override_settings(SEASON_BREAKS_EXPORT_ENDPOINT='')
    def test_missing_endpoint_publishes_without_queueing(self):
        self.publish()
        self.assertFalse(ExportJob.objects.exists())

    @patch('feedbackexport.jobs.create_season_breaks_job', side_effect=RuntimeError('boom'))
    def test_queueing_failure_never_blocks_publishing(self, create):
        with self.assertLogs('seasonbreaks.services', 'ERROR'):
            self.publish()
        create.assert_called_once()
        self.assertIsNotNone(self.season.public_snapshot)
        self.assertIsNotNone(self.season.public_published_at)

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_server_errors_retry_the_identical_body(self, http):
        http.side_effect = urllib.error.HTTPError(ENDPOINT, 503, '', {}, io.BytesIO(b'{"error": {"code": "retry"}}'))
        self.publish()
        worker_tick()
        job = ExportJob.objects.get()
        self.assertEqual(job.status, 'waiting')
        self.assertEqual(SeasonBreaksExportEvent.objects.get().status, 'failed')
        job.items.update(next_attempt_at=None)
        http.side_effect = ok_response
        worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        first, second = self.sent_requests(http)
        self.assertEqual(first.data, second.data)
        self.assertEqual(first.get_header('Idempotency-key'), second.get_header('Idempotency-key'))

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_validation_errors_fail_the_record_with_the_dr_message(self, http):
        body = b'{"error": {"code": "validation_error", "message": "Invalid integer: snapshot.season.id"}}'
        http.side_effect = urllib.error.HTTPError(ENDPOINT, 400, '', {}, io.BytesIO(body))
        self.publish()
        worker_tick()
        event = SeasonBreaksExportEvent.objects.get()
        self.assertEqual((event.status, event.last_http_status), ('permanent_failed', 400))
        self.assertIn('snapshot.season.id', event.last_error)
        self.assertEqual(ExportJob.objects.get().status, 'completed_errors')

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_404_blocks_the_season_breaks_stream(self, http):
        http.side_effect = urllib.error.HTTPError(ENDPOINT, 404, '', {}, io.BytesIO(b'{"detail": "Not found."}'))
        self.publish()
        worker_tick()
        job = ExportJob.objects.get()
        self.assertEqual(job.status, 'blocked')
        self.assertIn('SDA_JUDGES_SEASON_BREAKS_API_URL', job.blocked_types['breaks'])
        self.assertEqual(job.items.get().attempts, 0)
        control_job(job.id, 'resume')
        http.side_effect = ok_response
        worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')

    @override_settings(SEASON_BREAKS_EXPORT_TOKEN='', RESULTS_EXPORT_TOKEN='', FEEDBACK_EXPORT_TOKEN='fallback-secret')
    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=ok_response)
    def test_token_falls_back_like_the_results_token(self, http):
        self.publish()
        worker_tick()
        self.assertEqual(http.call_args.args[0].get_header('Authorization'), 'Bearer fallback-secret')

    def test_job_for_an_unpublished_season_fails_its_item(self):
        job = create_season_breaks_job(season_ids=[self.season.id])
        worker_tick()
        job.refresh_from_db()
        item = job.items.get()
        self.assertEqual(item.status, 'failed')
        self.assertIn('Publish it first', item.last_error)

    def test_tournament_jobs_reject_the_season_breaks_type(self):
        with self.assertRaises(ValueError):
            create_job(tournament_ids=[Tournament.objects.first().id], kinds=['breaks'])

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=ok_response)
    def test_queue_command_only_enqueues_published_seasons(self, http):
        self.publish()
        ExportJob.objects.all().delete()
        out = io.StringIO()
        call_command('feedbackexport', 'queue-season-breaks', '--season', self.season.slug, stdout=out)
        job = ExportJob.objects.get(pk=json.loads(out.getvalue())['job_id'])
        self.assertEqual(job.seasons[0]['id'], self.season.id)
        http.assert_not_called()


@override_settings(**BREAKS_SETTINGS)
class SeasonBreaksAdminPageTests(SeasonBreaksFixtureMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(username='breaks-editor')
        for permission in (BreaksPermission.VIEW, BreaksPermission.EDIT):
            GlobalBreaksPermission.objects.create(user=self.user, permission=permission)
        self.client.force_login(self.user)
        self.url = reverse('seasonbreaks-season-overview', kwargs={'season_slug': self.season.slug})

    def test_publish_form_queues_the_export(self):
        response = self.client.post(self.url, {'action': 'publish_public_snapshot'})
        self.assertRedirects(response, self.url)
        self.assertEqual(ExportJob.objects.get().requested_by, self.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'Databáza SDA')
        self.assertEqual(response.context['dr_export']['job'], ExportJob.objects.get())
        # Only export viewers get a link to the job page.
        self.assertNotContains(response, reverse('feedbackexport-job', args=[ExportJob.objects.get().id]))

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=ok_response)
    def test_page_shows_last_send_status(self, http):
        self.publish()
        worker_tick()
        response = self.client.get(self.url)
        status = response.context['dr_export']
        self.assertIsNone(status['job'])
        self.assertTrue(status['current'])
        self.assertEqual(status['event'].status, 'sent')
        self.assertContains(response, 'HTTP 201')
        self.assertContains(response, 'send_season_breaks_to_dr')

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=ok_response)
    def test_status_flags_an_earlier_snapshot_until_the_new_one_is_sent(self, http):
        self.publish()
        worker_tick()
        with override_settings(**DISABLED_SETTINGS):
            self.publish()
        status = season_breaks_export_status(self.season)
        self.assertEqual(status['event'].status, 'sent')
        self.assertFalse(status['current'])

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=ok_response)
    def test_send_again_resends_the_same_snapshot_with_the_same_key(self, http):
        self.publish()
        worker_tick()
        response = self.client.post(self.url, {'action': 'send_season_breaks_to_dr'})
        self.assertRedirects(response, self.url)
        job = ExportJob.objects.order_by('-id').first()
        self.assertTrue(job.force)
        worker_tick()
        first, second = self.sent_requests(http)
        self.assertEqual(first.data, second.data)
        self.assertEqual(first.get_header('Idempotency-key'), second.get_header('Idempotency-key'))
        self.assertEqual(SeasonBreaksExportEvent.objects.count(), 1)

    def test_send_again_needs_a_published_snapshot(self):
        response = self.client.post(self.url, {'action': 'send_season_breaks_to_dr'}, follow=True)
        self.assertContains(response, _("Publish the public snapshot before sending it to Databáza SDA."))
        self.assertFalse(ExportJob.objects.exists())

    @override_settings(**DISABLED_SETTINGS)
    def test_disabled_stream_hides_send_again(self):
        self.publish()
        response = self.client.get(self.url)
        self.assertContains(response, _("Sending season breaks to Databáza SDA is turned off or not configured."))
        self.assertNotContains(response, 'send_season_breaks_to_dr')
        response = self.client.post(self.url, {'action': 'send_season_breaks_to_dr'})
        self.assertFalse(ExportJob.objects.exists())

    def test_viewers_cannot_send(self):
        viewer = get_user_model().objects.create_user(username='breaks-viewer')
        GlobalBreaksPermission.objects.create(user=viewer, permission=BreaksPermission.VIEW)
        self.publish()
        ExportJob.objects.all().delete()
        self.client.force_login(viewer)
        response = self.client.post(self.url, {'action': 'send_season_breaks_to_dr'})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ExportJob.objects.exists())


class SeasonBreaksSettingsTests(TestCase):
    """Environment handling in settings/core.py."""

    CORE = Path(__file__).resolve().parents[2] / 'settings' / 'core.py'

    def load(self, **env):
        names = [name for name in os.environ if name.startswith('SDA_JUDGES_') or 'EXPORT' in name]
        with patch.dict(os.environ, {}, clear=False):
            for name in names:
                del os.environ[name]
            os.environ.update(env)
            return runpy.run_path(str(self.CORE))

    def test_endpoint_defaults_to_the_results_host(self):
        values = self.load(SDA_JUDGES_RESULTS_API_URL='https://rozhodcovia.example.test/api/v1/results/')
        self.assertEqual(values['SEASON_BREAKS_EXPORT_ENDPOINT'], 'https://rozhodcovia.example.test/api/v1/season-breaks/')

    def test_explicit_endpoint_wins_and_blank_counts_as_unset(self):
        values = self.load(SDA_JUDGES_SEASON_BREAKS_API_URL='https://other.example.test/breaks/')
        self.assertEqual(values['SEASON_BREAKS_EXPORT_ENDPOINT'], 'https://other.example.test/breaks/')
        values = self.load(SDA_JUDGES_SEASON_BREAKS_API_URL='', SDA_JUDGES_FEEDBACK_API_URL='https://fb.example.test/api/v1/feedback/')
        self.assertEqual(values['SEASON_BREAKS_EXPORT_ENDPOINT'], 'https://fb.example.test/api/v1/season-breaks/')

    def test_switch_follows_results_unless_set(self):
        self.assertTrue(self.load(SDA_JUDGES_RESULTS_EXPORT_ENABLED='1')['SEASON_BREAKS_EXPORT_ENABLED'])
        self.assertTrue(self.load(SDA_JUDGES_RESULTS_EXPORT_ENABLED='1', SDA_JUDGES_SEASON_BREAKS_EXPORT_ENABLED='')['SEASON_BREAKS_EXPORT_ENABLED'])
        self.assertFalse(self.load(SDA_JUDGES_RESULTS_EXPORT_ENABLED='1', SDA_JUDGES_SEASON_BREAKS_EXPORT_ENABLED='0')['SEASON_BREAKS_EXPORT_ENABLED'])
        self.assertTrue(self.load(SDA_JUDGES_SEASON_BREAKS_EXPORT_ENABLED='1')['SEASON_BREAKS_EXPORT_ENABLED'])
        self.assertFalse(self.load()['SEASON_BREAKS_EXPORT_ENABLED'])

    def test_token_is_the_results_token(self):
        values = self.load(SDA_JUDGES_RESULTS_API_TOKEN='r' * 40)
        self.assertEqual(values['SEASON_BREAKS_EXPORT_TOKEN'], 'r' * 40)
        values = self.load(SDA_JUDGES_FEEDBACK_API_TOKEN='f' * 40)
        self.assertEqual(values['SEASON_BREAKS_EXPORT_TOKEN'], 'f' * 40)
