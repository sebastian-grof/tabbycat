from django.test import TestCase

from adjallocation.models import DebateAdjudicator
from adjfeedback.forms import BaseFeedbackForm
from adjfeedback.models import AdjudicatorFeedback
from draw.models import Debate
from participants.models import Adjudicator, Institution
from tournaments.models import Round, Tournament


class FeedbackScoreToggleTests(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create()
        self.round = Round.objects.create(tournament=self.tournament, seq=1, abbreviation="R1")
        self.institution = Institution.objects.create(code="I", name="Institution")
        self.adjudicator = Adjudicator.objects.create(
            tournament=self.tournament, institution=self.institution, name="Adj", base_score=3,
        )
        self.debate = Debate.objects.create(round=self.round)
        self.debate_adjudicator = DebateAdjudicator.objects.create(
            debate=self.debate, adjudicator=self.adjudicator, type=DebateAdjudicator.TYPE_CHAIR,
        )

    def make_form_class(self):
        class FeedbackForm(BaseFeedbackForm):
            _tournament = self.tournament
            question_filter = {}

        return FeedbackForm

    def test_score_field_shown_by_default(self):
        form = self.make_form_class()()
        self.assertIn('score', form.fields)

    def test_score_field_hidden_and_ignored_when_disabled(self):
        self.tournament.preferences['feedback__feedback_affects_adjudicator_scores'] = False
        form = self.make_form_class()(data={})

        self.assertNotIn('score', form.fields)
        self.assertTrue(form.is_valid())

        feedback = form.save_adjudicatorfeedback(
            adjudicator=self.adjudicator,
            source_adjudicator=self.debate_adjudicator,
            source_team=None,
            submitter_type=AdjudicatorFeedback.Submitter.PUBLIC,
        )
        self.assertEqual(feedback.score, self.adjudicator.base_score)
        self.assertTrue(feedback.ignored)

    def test_weighted_score_ignores_feedback_when_disabled(self):
        AdjudicatorFeedback.objects.create(
            adjudicator=self.adjudicator,
            source_adjudicator=self.debate_adjudicator,
            score=5,
            confirmed=True,
            ignored=False,
            submitter_type=AdjudicatorFeedback.Submitter.PUBLIC,
        )

        self.assertEqual(self.adjudicator.weighted_score(1), 5)

        self.tournament.preferences['feedback__feedback_affects_adjudicator_scores'] = False
        adjudicator = Adjudicator.objects.get(pk=self.adjudicator.pk)
        self.assertEqual(adjudicator.weighted_score(1), self.adjudicator.base_score)
