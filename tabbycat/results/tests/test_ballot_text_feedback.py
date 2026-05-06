from django.contrib.auth import get_user_model
from django.test import TestCase

from draw.models import Debate
from participants.models import Adjudicator, Institution
from results.forms import BallotTextFeedbackForm
from results.models import BallotSubmission, BallotTextFeedback
from results.views import ballot_text_feedbacks_for_debate
from tournaments.models import Round, Tournament
from venues.models import Venue


class BallotTextFeedbackFormTests(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug="btf", name="Ballot Text Feedback")
        self.round = Round.objects.create(tournament=self.tournament, seq=1, abbreviation="R1")
        self.venue = Venue.objects.create(name="Venue", priority=1)
        self.debate = Debate.objects.create(round=self.round, venue=self.venue)
        self.ballot = BallotSubmission.objects.create(
            debate=self.debate,
            submitter_type=BallotSubmission.Submitter.TABROOM,
            confirmed=True,
        )
        self.institution = Institution.objects.create(code="Adj", name="Adjudicators")
        self.adjudicator = Adjudicator.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            name="Adjudicator",
            base_score=5,
        )
        self.user = get_user_model().objects.create_user(username="tab", password="pass")

    def test_save_creates_updates_and_deletes_feedback(self):
        form = BallotTextFeedbackForm(data={'text': 'Useful team feedback.'})
        self.assertTrue(form.is_valid())
        feedback = form.save(self.ballot, adjudicator=self.adjudicator, user=self.user)

        self.assertEqual(feedback.text, 'Useful team feedback.')
        self.assertEqual(feedback.updated_by_adjudicator, self.adjudicator)
        self.assertEqual(feedback.updated_by_user, self.user)

        form = BallotTextFeedbackForm(data={'text': 'Updated feedback.'})
        self.assertTrue(form.is_valid())
        updated = form.save(self.ballot, adjudicator=self.adjudicator, user=self.user)

        self.assertEqual(updated.id, feedback.id)
        self.assertEqual(updated.text, 'Updated feedback.')

        form = BallotTextFeedbackForm(data={'text': '   '})
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.save(self.ballot, adjudicator=self.adjudicator, user=self.user))
        self.assertFalse(BallotTextFeedback.objects.filter(ballot_submission=self.ballot).exists())

    def test_initial_text_prefills_form(self):
        form = BallotTextFeedbackForm(initial_text="Already saved")

        self.assertEqual(form['text'].value(), "Already saved")

    def test_feedbacks_for_debate_ignores_discarded_ballots(self):
        BallotTextFeedback.objects.create(ballot_submission=self.ballot, text="Visible")
        discarded = BallotSubmission.objects.create(
            debate=self.debate,
            submitter_type=BallotSubmission.Submitter.TABROOM,
            discarded=True,
        )
        BallotTextFeedback.objects.create(ballot_submission=discarded, text="Hidden")

        feedbacks = list(ballot_text_feedbacks_for_debate(self.debate))

        self.assertEqual(len(feedbacks), 1)
        self.assertEqual(feedbacks[0].text, "Visible")
