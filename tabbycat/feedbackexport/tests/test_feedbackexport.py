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
from results.models import Submission
from tournaments.models import Round, Tournament

from feedbackexport.models import FeedbackExportEvent, JudgeProfile, JudgeProfileLink
from feedbackexport.services import build_feedback_payload, queue_feedback_export


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
        self.assertEqual(payload['target']['judge_profile']['external_id'], 'judge-1')
        self.assertEqual(payload['source']['type'], 'team')
        self.assertEqual(payload['answers'][0]['reference'], 'clarity')
        self.assertEqual(payload['answers'][0]['answer'], 5)
        self.assertNotIn('ip_address', payload)
        self.assertNotIn('private_url', payload)

    @override_settings(FEEDBACK_EXPORT_ENABLED=False)
    def test_index_requires_feedback_export_permission_or_superuser(self):
        user = get_user_model().objects.create_user(username='tab', password='pw')
        self.client.login(username='tab', password='pw')
        self.assertEqual(self.client.get(reverse('feedbackexport-index')).status_code, 403)

        superuser = get_user_model().objects.create_superuser(username='root', password='pw')
        self.client.force_login(superuser)
        self.assertEqual(self.client.get(reverse('feedbackexport-index')).status_code, 200)
