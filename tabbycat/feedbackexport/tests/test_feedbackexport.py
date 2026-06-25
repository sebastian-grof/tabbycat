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
from breakqual.models import BreakCategory
from draw.models import Debate, DebateTeam
from participants.models import Adjudicator, Institution, Team
from registration.models import Answer, Question
from results.models import BallotSubmission, Submission
from seasonbreaks.models import BreakLeague, BreakRegion, BreakSeason, BreakTournament
from seasonbreaks.services import freeze_break_tournament
from tournaments.models import Round, Tournament

from feedbackexport.models import AdjudicatorStatsExportEvent, FeedbackExportEvent
from feedbackexport.services import (
    adjudicator_stats_event_needs_reexport,
    build_adjudicator_stats_payload,
    build_feedback_payload,
    queue_adjudicator_stats_export,
    queue_feedback_export,
    send_adjudicator_stats_event,
    send_event,
    validate_feedback_payload,
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

    def test_feedback_export_queues_without_local_judge_mapping(self):
        event = queue_feedback_export(self.feedback)
        self.assertEqual(event.status, FeedbackExportEvent.Status.PENDING)
        self.assertIsNone(event.payload['target']['judge_profile_id'])
        self.assertEqual(event.payload['target']['local_adjudicator_id'], self.adjudicator.id)
        self.assertEqual(event.payload['target']['email'], 'target@example.test')

    def test_payload_contains_feedback_context_without_private_fields(self):

        event = queue_feedback_export(self.feedback)
        payload = event.payload

        self.assertEqual(event.status, FeedbackExportEvent.Status.PENDING)
        self.assertEqual(payload['source_system'], 'tabbycat-sda')
        self.assertTrue(payload['idempotency_key'].startswith('tabbycat-sda:feedback:%s:' % self.feedback.id))
        self.assertTrue(payload['idempotency_key'].endswith(':v2'))
        self.assertEqual(event.idempotency_key, payload['idempotency_key'])
        self.assertIsNone(payload['target']['judge_profile_id'])
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

    def test_sdl_team_comment_uses_dr_comment_reference(self):
        comment_question = AdjudicatorFeedbackQuestion.objects.create(
            tournament=self.tournament,
            for_content_type=ContentType.objects.get_for_model(AdjudicatorFeedback),
            seq=2,
            text='Komentáre k rozhodnutiu',
            name='Komentáre k rozhodnutiu',
            answer_type=Question.AnswerType.LONGTEXT,
            required=False,
            reference='komentare_k_rozhodnutiu',
            from_adj=False,
            from_team=True,
        )
        Answer.objects.create(
            content_object=self.feedback,
            question=comment_question,
            answer='Decision was explained clearly.',
        )

        payload = build_feedback_payload(self.feedback)
        answers = {answer['question_reference']: answer for answer in payload['answers']}

        self.assertEqual(answers['comment']['value'], 'Decision was explained clearly.')
        self.assertNotIn('komentare_k_rozhodnutiu', answers)

    def test_sdl_adjudicator_assessment_uses_dr_references(self):
        assessment_question = AdjudicatorFeedbackQuestion.objects.create(
            tournament=self.tournament,
            for_content_type=ContentType.objects.get_for_model(AdjudicatorFeedback),
            seq=2,
            text='Posudok',
            name='Posudok',
            answer_type=Question.AnswerType.SINGLE_SELECT,
            required=True,
            reference='posudok',
            choices=['Pozitívny', 'Neutrálny', 'Negatívny'],
            from_adj=True,
            from_team=False,
        )
        comment_question = AdjudicatorFeedbackQuestion.objects.create(
            tournament=self.tournament,
            for_content_type=ContentType.objects.get_for_model(AdjudicatorFeedback),
            seq=3,
            text='Komentáre',
            name='Komentáre',
            answer_type=Question.AnswerType.LONGTEXT,
            required=False,
            reference='komentare_rozhodca',
            from_adj=True,
            from_team=False,
        )
        feedback = AdjudicatorFeedback.objects.create(
            adjudicator=self.adjudicator,
            score=4,
            source_adjudicator=self.source_debate_adjudicator,
            submitter_type=Submission.Submitter.PUBLIC,
            confirmed=True,
            confirm_timestamp=timezone.now(),
        )
        Answer.objects.create(
            content_object=feedback,
            question=assessment_question,
            answer='Pozitívny',
        )
        Answer.objects.create(
            content_object=feedback,
            question=comment_question,
            answer='Strong chairing and useful feedback.',
        )

        payload = build_feedback_payload(feedback)
        answers = {answer['question_reference']: answer for answer in payload['answers']}

        self.assertEqual(answers['assessment']['value'], 'Pozitívny')
        self.assertEqual(answers['assessment_comment']['value'], 'Strong chairing and useful feedback.')
        self.assertNotIn('posudok', answers)
        self.assertNotIn('komentare_rozhodca', answers)

    def test_payload_contains_break_league_when_tournament_is_in_break_season(self):
        self._break_tournament()

        payload = build_feedback_payload(self.feedback)

        self.assertEqual(payload['tournament']['season'], '2025/2026')
        self.assertEqual(payload['tournament']['league'], 'SDL')
        self.assertEqual(payload['tournament']['league_slug'], 'sdl')

    def test_payload_contains_adjudicator_source(self):
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
        self.feedback.ignored = True
        self.feedback.save()

        payload = build_feedback_payload(self.feedback)

        self.assertIs(payload['ignored'], True)

    def test_disabled_feedback_scoring_does_not_mark_export_ignored(self):
        self.tournament.preferences['feedback__feedback_affects_adjudicator_scores'] = False

        payload = build_feedback_payload(self.feedback)

        self.assertIs(payload['ignored'], False)
        self.assertIs(payload['feedback_affects_adjudicator_scores'], False)
        self.assertIs(payload['score_ignored_in_tabbycat'], True)

    @override_settings(FEEDBACK_EXPORT_ENDPOINT='https://example.test/api/', FEEDBACK_EXPORT_TOKEN='secret')
    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_send_event_posts_authorization_and_idempotency_headers(self, urlopen):
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
        event = queue_feedback_export(self.feedback)
        urlopen.side_effect = urllib.error.HTTPError(
            'https://example.test/api/', 500, 'Server error', hdrs=None, fp=io.BytesIO(b'{}'),
        )

        send_event(event)

        event.refresh_from_db()
        self.assertEqual(event.status, FeedbackExportEvent.Status.FAILED)
        self.assertEqual(event.last_http_status, 500)

    def test_validate_feedback_payload_rejects_blank_source_name(self):
        payload = build_feedback_payload(self.feedback)
        self.assertTrue(payload['source']['display_name'])  # sanity: name present by default

        payload['source']['display_name'] = ''
        with self.assertRaises(ValueError):
            validate_feedback_payload(payload)

    def test_idempotency_key_changes_when_payload_content_changes(self):
        event = queue_feedback_export(self.feedback)
        first_key = event.idempotency_key
        self.assertIn(':feedback:%s:' % self.feedback.id, first_key)
        self.assertEqual(event.payload['idempotency_key'], first_key)

        # A change to the exported content must yield a new idempotency key, so DR
        # records it as a fresh import instead of rejecting the resend with HTTP 409.
        self.feedback.score = 2
        self.feedback.save()
        event = queue_feedback_export(self.feedback, force=True)

        self.assertNotEqual(event.idempotency_key, first_key)
        self.assertEqual(event.payload['idempotency_key'], event.idempotency_key)
        self.assertEqual(event.status, FeedbackExportEvent.Status.PENDING)

    @override_settings(FEEDBACK_EXPORT_ENDPOINT='https://example.test/api/', FEEDBACK_EXPORT_TOKEN='secret')
    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_send_event_records_api_response_body_in_last_error(self, urlopen):
        event = queue_feedback_export(self.feedback)
        urlopen.side_effect = urllib.error.HTTPError(
            'https://example.test/api/', 422, 'Unprocessable Entity', hdrs=None,
            fp=io.BytesIO(b'{"detail": "source.name is required"}'),
        )

        send_event(event)

        event.refresh_from_db()
        self.assertEqual(event.status, FeedbackExportEvent.Status.PERMANENT_FAILED)
        self.assertEqual(event.last_http_status, 422)
        self.assertIn('source.name is required', event.last_error)
        self.assertEqual(event.remote_response, {'detail': 'source.name is required'})

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

    def test_judge_activity_page_queues_only_selected_tournaments(self):
        other_tournament = Tournament.objects.create(name='Other Tournament', short_name='OT', slug='ot')
        superuser = get_user_model().objects.create_superuser(username='root', password='pw')
        self.client.force_login(superuser)

        response = self.client.post(reverse('feedbackexport-activity'), {
            'action': 'queue_selected',
            'tournaments': [str(self.tournament.id)],
        })

        self.assertRedirects(response, reverse('feedbackexport-activity'))
        self.assertTrue(AdjudicatorStatsExportEvent.objects.filter(source_tournament_id=self.tournament.id).exists())
        self.assertFalse(AdjudicatorStatsExportEvent.objects.filter(source_tournament_id=other_tournament.id).exists())

    def _break_tournament(self):
        league = BreakLeague.objects.get(slug='sdl')
        season = BreakSeason.objects.create(
            name='SDL 2025/2026', slug='sdl-2025-2026', league=league,
        )
        region = BreakRegion.objects.create(season=season, name='West')
        return BreakTournament.objects.create(season=season, tournament=self.tournament, region=region)

    def test_freeze_break_tournament_does_not_queue_adjudicator_stats_event(self):
        break_tournament = self._break_tournament()
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)

        with self.captureOnCommitCallbacks(execute=True):
            freeze_break_tournament(break_tournament)

        self.assertFalse(AdjudicatorStatsExportEvent.objects.exists())

    def test_queue_adjudicator_stats_event_uses_tournament_payload_with_break_metadata(self):
        break_tournament = self._break_tournament()
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)

        event = queue_adjudicator_stats_export(self.tournament)

        self.assertEqual(event.status, AdjudicatorStatsExportEvent.Status.PENDING)
        self.assertEqual(event.tournament, self.tournament)
        self.assertEqual(event.break_tournament, break_tournament)
        self.assertEqual(event.source_tournament_id, self.tournament.id)
        self.assertEqual(event.payload['version'], 2)
        self.assertEqual(event.payload['season']['slug'], 'sdl-2025-2026')
        self.assertEqual(event.payload['season']['league'], 'SDL')
        self.assertEqual(event.payload['season']['league_slug'], 'sdl')
        self.assertEqual(event.payload['tournament']['id'], self.tournament.id)
        self.assertEqual(event.payload['tournament']['season'], '2025/2026')
        self.assertEqual(event.payload['break_tournament']['region']['name'], 'West')
        self.assertEqual(event.payload['break_tournament']['region']['slug'], 'west')
        row = {row['name']: row for row in event.payload['adjudicators']}['Target Judge']
        self.assertIsNone(row['judge_profile_id'])
        self.assertEqual(row['local_adjudicator_id'], self.adjudicator.id)
        self.assertEqual(row['chair_count'], 1)
        self.assertEqual(row['panellist_count'], 0)
        self.assertEqual(row['trainee_count'], 0)
        self.assertEqual(row['total_count'], 1)

    def test_adjudicator_stats_payload_keeps_trainee_separate_from_total(self):
        self._break_tournament()
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        trainee = Adjudicator.objects.create(
            tournament=self.tournament, name='Trainee Judge', email='trainee@example.test',
        )
        DebateAdjudicator.objects.create(
            debate=self.debate, adjudicator=trainee, type=DebateAdjudicator.TYPE_TRAINEE,
        )

        payload = build_adjudicator_stats_payload(self.tournament)
        rows = {row['name']: row for row in payload['adjudicators']}

        self.assertEqual(payload['version'], 2)
        self.assertEqual(payload['season']['name'], 'SDL 2025/2026')
        self.assertEqual(payload['tournament']['season'], '2025/2026')
        self.assertEqual(rows['Target Judge']['total_count'], 1)
        self.assertEqual(rows['Trainee Judge']['trainee_count'], 1)
        self.assertEqual(rows['Trainee Judge']['total_count'], 0)

    def test_adjudicator_stats_payload_includes_confirmed_elimination_debates(self):
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        break_category = BreakCategory.objects.create(
            tournament=self.tournament,
            name='Open',
            slug='open',
            seq=1,
            break_size=2,
            is_general=True,
            priority=1,
        )
        elim_round = Round.objects.create(
            tournament=self.tournament, seq=2, name='Final', abbreviation='GF',
            stage=Round.Stage.ELIMINATION, draw_type=Round.DrawType.ELIMINATION,
            break_category=break_category,
        )
        elim_debate = Debate.objects.create(round=elim_round, bracket=1, room_rank=1)
        DebateAdjudicator.objects.create(
            debate=elim_debate, adjudicator=self.adjudicator, type=DebateAdjudicator.TYPE_CHAIR,
        )
        BallotSubmission.objects.create(debate=elim_debate, confirmed=True)

        payload = build_adjudicator_stats_payload(self.tournament)
        row = {row['name']: row for row in payload['adjudicators']}['Target Judge']

        self.assertEqual(row['chair_count'], 2)
        self.assertEqual(row['total_count'], 2)

    def test_tournament_without_break_metadata_can_export_judge_activity(self):
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)

        event = queue_adjudicator_stats_export(self.tournament)

        self.assertEqual(event.status, AdjudicatorStatsExportEvent.Status.PENDING)
        self.assertIsNone(event.break_tournament)
        self.assertIsNone(event.payload['season'])
        self.assertIsNone(event.payload['break_tournament'])
        self.assertEqual(event.payload['tournament']['id'], self.tournament.id)

    def test_removing_break_tournament_does_not_delete_judge_activity_event(self):
        break_tournament = self._break_tournament()
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        event = queue_adjudicator_stats_export(self.tournament)

        break_tournament.delete()
        event.refresh_from_db()

        self.assertIsNone(event.break_tournament)
        self.assertEqual(event.tournament, self.tournament)
        self.assertEqual(event.source_tournament_id, self.tournament.id)

    def test_sent_judge_activity_event_marks_needs_reexport_when_payload_changes(self):
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        event = queue_adjudicator_stats_export(self.tournament)
        event.mark_sent()

        self.assertFalse(adjudicator_stats_event_needs_reexport(event, self.tournament))

        second_round = Round.objects.create(
            tournament=self.tournament, seq=2, name='Round 2', abbreviation='R2',
            draw_type=Round.DrawType.RANDOM,
        )
        second_debate = Debate.objects.create(round=second_round, bracket=1, room_rank=1)
        DebateAdjudicator.objects.create(
            debate=second_debate, adjudicator=self.adjudicator, type=DebateAdjudicator.TYPE_CHAIR,
        )
        BallotSubmission.objects.create(debate=second_debate, confirmed=True)

        self.assertTrue(adjudicator_stats_event_needs_reexport(event, self.tournament))

    @override_settings(ADJUDICATOR_STATS_EXPORT_ENDPOINT='https://example.test/stats/', ADJUDICATOR_STATS_EXPORT_TOKEN='secret')
    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_send_adjudicator_stats_event_posts_authorization_and_idempotency_headers(self, urlopen):
        self._break_tournament()
        BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        event = queue_adjudicator_stats_export(self.tournament)
        urlopen.return_value = FakeHTTPResponse(status=201)

        send_adjudicator_stats_event(event)

        request = urlopen.call_args.args[0]
        self.assertEqual(request.headers['Authorization'], 'Bearer secret')
        self.assertEqual(request.headers['Idempotency-key'], event.idempotency_key)
        event.refresh_from_db()
        self.assertEqual(event.status, AdjudicatorStatsExportEvent.Status.SENT)
