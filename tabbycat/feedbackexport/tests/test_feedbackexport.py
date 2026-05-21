import io
import urllib.error
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from adjallocation.models import DebateAdjudicator
from adjfeedback.models import AdjudicatorFeedback, AdjudicatorFeedbackQuestion
from draw.models import Debate, DebateTeam
from participants.models import Adjudicator, Institution, Team
from registration.models import Answer, Question
from results.models import BallotSubmission, Submission
from seasonbreaks.models import BreakLeague, BreakRegion, BreakSeason, BreakTournament
from seasonbreaks.services import freeze_break_tournament
from tournaments.models import Round, Tournament

from feedbackexport.models import AdjudicatorStatsExportEvent, FeedbackExportEvent, JudgeProfile, JudgeProfileLink
from feedbackexport.services import (
    build_adjudicator_stats_payload,
    build_feedback_payload,
    queue_adjudicator_stats_export,
    queue_feedback_export,
    send_adjudicator_stats_event,
    send_event,
)


class FakeHTTPResponse:
    def __init__(self, status=201, body=b'{"ok": true}'):
        self.status = status
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class FeedbackExportTestCase(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(name='Test Tournament', short_name='TT', slug='tt')
        self.round = Round.objects.create(
            tournament=self.tournament, seq=1, name='Round 1', abbreviation='R1',
            draw_type=Round.DrawType.RANDOM,
        )
        self.institution = Institution.objects.create(name='Institution', code='INST')
        self.team = Team.objects.create(
            tournament=self.tournament, institution=self.institution,
            reference='Team A', short_reference='A', use_institution_prefix=False,
        )
        self.debate = Debate.objects.create(round=self.round, bracket=1, room_rank=3)
        self.debate_team = DebateTeam.objects.create(debate=self.debate, team=self.team, side=0)
        self.adjudicator = Adjudicator.objects.create(
            tournament=self.tournament, name='Target Judge', email='target@example.test', institution=self.institution,
        )
        self.debate_adjudicator = DebateAdjudicator.objects.create(
            debate=self.debate, adjudicator=self.adjudicator, type=DebateAdjudicator.TYPE_CHAIR,
        )
        self.source_adjudicator = Adjudicator.objects.create(
            tournament=self.tournament, name='Source Judge', email='source@example.test', institution=self.institution,
        )
        self.source_debate_adjudicator = DebateAdjudicator.objects.create(
            debate=self.debate, adjudicator=self.source_adjudicator, type=DebateAdjudicator.TYPE_PANEL,
        )
        self.question = AdjudicatorFeedbackQuestion.objects.create(
            tournament=self.tournament,
            for_content_type=ContentType.objects.get_for_model(AdjudicatorFeedback),
            seq=1,
            text='Was the judge clear?',
            name='Clarity',
            answer_type=Question.AnswerType.INTEGER_SCALE,
            required=True,
            min_value=1,
            max_value=5,
            reference='clarity',
            from_adj=True,
            from_team=True,
        )
        self.feedback = AdjudicatorFeedback.objects.create(
            adjudicator=self.adjudicator,
            score=4,
            source_team=self.debate_team,
            submitter_type=Submission.Submitter.PUBLIC,
            confirmed=True,
            confirm_timestamp=timezone.now(),
        )
        Answer.objects.create(
            content_object=self.feedback,
            question=self.question,
            answer='5',
        )

    def test_missing_judge_profile_blocks_export_event(self):
        event = queue_feedback_export(self.feedback)
        self.assertEqual(event.status, FeedbackExportEvent.Status.PERMANENT_FAILED)
        self.assertIn('not linked', event.last_error)
        self.assertIsNone(event.payload)

    def test_payload_contains_feedback_context_without_private_fields(self):
        profile = JudgeProfile.objects.create(name='Canonical Judge', primary_email='target@example.test', external_id='judge-1')
        JudgeProfileLink.objects.create(profile=profile, adjudicator=self.adjudicator)

        event = queue_feedback_export(self.feedback)
        payload = event.payload

        self.assertEqual(event.status, FeedbackExportEvent.Status.PENDING)
        self.assertEqual(payload['source_system'], 'tabbycat-sda')
        self.assertEqual(payload['idempotency_key'], 'tabbycat-sda:feedback:%s:v1' % self.feedback.id)
        self.assertEqual(payload['target']['judge_profile_id'], 'judge-1')
        self.assertEqual(payload['target']['local_adjudicator_id'], self.adjudicator.id)
        self.assertEqual(payload['target']['role'], 'chair')
        self.assertEqual(payload['source']['type'], 'team')
        self.assertEqual(payload['source']['local_id'], self.team.id)
        self.assertEqual(payload['source']['display_name'], self.team.short_name)
        self.assertEqual(payload['answers'][0]['question_reference'], 'clarity')
        self.assertEqual(payload['answers'][0]['answer_type'], 'integer')
        self.assertEqual(payload['answers'][0]['value'], 5)
        self.assertNotIn('ip_address', payload)
        self.assertNotIn('private_url', payload)
        self.assertNotIn('submitter', payload)

    def test_payload_contains_break_league_when_tournament_is_in_break_season(self):
        profile = JudgeProfile.objects.create(name='Canonical Judge', primary_email='target@example.test', external_id='judge-1')
        JudgeProfileLink.objects.create(profile=profile, adjudicator=self.adjudicator)
        self._break_tournament()

        payload = build_feedback_payload(self.feedback)

        self.assertEqual(payload['tournament']['season'], '2025/2026')
        self.assertEqual(payload['tournament']['league'], 'SDL')
        self.assertEqual(payload['tournament']['league_slug'], 'sdl')

    def test_payload_contains_adjudicator_source(self):
        profile = JudgeProfile.objects.create(name='Canonical Judge', primary_email='target@example.test', external_id='judge-1')
        JudgeProfileLink.objects.create(profile=profile, adjudicator=self.adjudicator)
        feedback = AdjudicatorFeedback.objects.create(
            adjudicator=self.adjudicator,
            score=3,
            source_adjudicator=self.source_debate_adjudicator,
            submitter_type=Submission.Submitter.PUBLIC,
            confirmed=True,
            confirm_timestamp=timezone.now(),
        )

        payload = build_feedback_payload(feedback)

        self.assertEqual(payload['source']['type'], 'adjudicator')
        self.assertEqual(payload['source']['local_id'], self.source_adjudicator.id)
        self.assertEqual(payload['source']['display_name'], 'Source Judge')
        self.assertEqual(payload['source']['email'], 'source@example.test')

    def test_ignored_feedback_is_exported_with_ignored_flag(self):
        profile = JudgeProfile.objects.create(name='Canonical Judge', primary_email='target@example.test')
        JudgeProfileLink.objects.create(profile=profile, adjudicator=self.adjudicator)
        self.feedback.ignored = True
        self.feedback.save()

        payload = build_feedback_payload(self.feedback)

        self.assertIs(payload['ignored'], True)

    def test_disabled_feedback_scoring_does_not_mark_export_ignored(self):
        self.tournament.preferences['feedback__feedback_affects_adjudicator_scores'] = False
        profile = JudgeProfile.objects.create(name='Canonical Judge', primary_email='target@example.test')
        JudgeProfileLink.objects.create(profile=profile, adjudicator=self.adjudicator)

        payload = build_feedback_payload(self.feedback)

        self.assertIs(payload['ignored'], False)
        self.assertIs(payload['feedback_affects_adjudicator_scores'], False)
        self.assertIs(payload['score_ignored_in_tabbycat'], True)

    @override_settings(FEEDBACK_EXPORT_ENDPOINT='https://example.test/api/', FEEDBACK_EXPORT_TOKEN='secret')
    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_send_event_posts_authorization_and_idempotency_headers(self, urlopen):
        profile = JudgeProfile.objects.create(name='Canonical Judge', primary_email='target@example.test')
        JudgeProfileLink.objects.create(profile=profile, adjudicator=self.adjudicator)
        event = queue_feedback_export(self.feedback)
        urlopen.return_value = FakeHTTPResponse(status=201)

        send_event(event)

        request = urlopen.call_args.args[0]
        self.assertEqual(request.headers['Authorization'], 'Bearer secret')
        self.assertEqual(request.headers['Idempotency-key'], event.idempotency_key)
        event.refresh_from_db()
        self.assertEqual(event.status, FeedbackExportEvent.Status.SENT)

    @override_settings(FEEDBACK_EXPORT_ENDPOINT='https://example.test/api/', FEEDBACK_EXPORT_TOKEN='secret')
    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_send_event_logs_api_error_without_crashing(self, urlopen):
        profile = JudgeProfile.objects.create(name='Canonical Judge', primary_email='target@example.test')
        JudgeProfileLink.objects.create(profile=profile, adjudicator=self.adjudicator)
        event = queue_feedback_export(self.feedback)
        urlopen.side_effect = urllib.error.HTTPError(
            'https://example.test/api/', 500, 'Server error', hdrs=None, fp=io.BytesIO(b'{}'),
        )

        send_event(event)

        event.refresh_from_db()
        self.assertEqual(event.status, FeedbackExportEvent.Status.FAILED)
        self.assertEqual(event.last_http_status, 500)

    @override_settings(FEEDBACK_EXPORT_ENABLED=False)
    @patch('feedbackexport.signals.queue_feedback_export')
    def test_disabled_live_export_does_not_queue_from_signal(self, queue_feedback):
        AdjudicatorFeedback.objects.create(
            adjudicator=self.adjudicator,
            score=4,
            source_adjudicator=self.source_debate_adjudicator,
            submitter_type=Submission.Submitter.PUBLIC,
            confirmed=True,
            confirm_timestamp=timezone.now(),
        )

        queue_feedback.assert_not_called()

    @override_settings(FEEDBACK_EXPORT_ENABLED=False)
    def test_index_requires_feedback_export_permission_or_superuser(self):
        user = get_user_model().objects.create_user(username='tab', password='pw')
        self.client.login(username='tab', password='pw')
        self.assertEqual(self.client.get(reverse('feedbackexport-index')).status_code, 403)

        superuser = get_user_model().objects.create_superuser(username='root', password='pw')
        self.client.force_login(superuser)
        self.assertEqual(self.client.get(reverse('feedbackexport-index')).status_code, 200)

    def _break_tournament(self):
        league = BreakLeague.objects.get(slug='sdl')
        season = BreakSeason.objects.create(
            name='SDL 2025/2026', slug='sdl-2025-2026', league=league,
        )
        region = BreakRegion.objects.create(season=season, name='West')
        return BreakTournament.objects.create(season=season, tournament=self.tournament, region=region)

    def test_freeze_break_tournament_queues_adjudicator_stats_event(self):
        profile = JudgeProfile.objects.create(name='Canonical Judge', primary_email='target@example.test', external_id='judge-1')
        JudgeProfileLink.objects.create(profile=profile, adjudicator=self.adjudicator)
        break_tournament = self._break_tournament()
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)

        with self.captureOnCommitCallbacks(execute=True):
            freeze_break_tournament(break_tournament)

        event = AdjudicatorStatsExportEvent.objects.get(break_tournament=break_tournament)
        self.assertEqual(event.status, AdjudicatorStatsExportEvent.Status.PENDING)
        self.assertEqual(event.payload['season']['slug'], 'sdl-2025-2026')
        self.assertEqual(event.payload['season']['league'], 'SDL')
        self.assertEqual(event.payload['season']['league_slug'], 'sdl')
        self.assertEqual(event.payload['tournament']['id'], self.tournament.id)
        self.assertEqual(event.payload['tournament']['season'], '2025/2026')
        self.assertEqual(event.payload['break_tournament']['region']['name'], 'West')
        self.assertEqual(event.payload['break_tournament']['region']['slug'], 'west')
        row = {row['name']: row for row in event.payload['adjudicators']}['Target Judge']
        self.assertEqual(row['judge_profile_id'], 'judge-1')
        self.assertEqual(row['local_adjudicator_id'], self.adjudicator.id)
        self.assertEqual(row['chair_count'], 1)
        self.assertEqual(row['panellist_count'], 0)
        self.assertEqual(row['trainee_count'], 0)
        self.assertEqual(row['total_count'], 1)

    def test_adjudicator_stats_payload_keeps_trainee_separate_from_total(self):
        break_tournament = self._break_tournament()
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        trainee = Adjudicator.objects.create(
            tournament=self.tournament, name='Trainee Judge', email='trainee@example.test',
        )
        DebateAdjudicator.objects.create(
            debate=self.debate, adjudicator=trainee, type=DebateAdjudicator.TYPE_TRAINEE,
        )
        with self.captureOnCommitCallbacks(execute=True):
            freeze_break_tournament(break_tournament)

        payload = build_adjudicator_stats_payload(break_tournament)
        rows = {row['name']: row for row in payload['adjudicators']}

        self.assertEqual(payload['season']['name'], 'SDL 2025/2026')
        self.assertEqual(payload['tournament']['season'], '2025/2026')
        self.assertEqual(rows['Target Judge']['total_count'], 1)
        self.assertEqual(rows['Trainee Judge']['trainee_count'], 1)
        self.assertEqual(rows['Trainee Judge']['total_count'], 0)

    @override_settings(ADJUDICATOR_STATS_EXPORT_ENDPOINT='https://example.test/stats/', ADJUDICATOR_STATS_EXPORT_TOKEN='secret')
    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_send_adjudicator_stats_event_posts_authorization_and_idempotency_headers(self, urlopen):
        break_tournament = self._break_tournament()
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        with self.captureOnCommitCallbacks(execute=True):
            freeze_break_tournament(break_tournament)
        event = queue_adjudicator_stats_export(break_tournament)
        urlopen.return_value = FakeHTTPResponse(status=201)

        send_adjudicator_stats_event(event)

        request = urlopen.call_args.args[0]
        self.assertEqual(request.headers['Authorization'], 'Bearer secret')
        self.assertEqual(request.headers['Idempotency-key'], event.idempotency_key)
        event.refresh_from_db()
        self.assertEqual(event.status, AdjudicatorStatsExportEvent.Status.SENT)
