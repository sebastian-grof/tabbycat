from django import forms
from django.test import TestCase

from adjallocation.models import DebateAdjudicator
from draw.models import Debate, DebateTeam
from draw.types import DebateSide
from participants.models import Adjudicator, Team
from results.forms import PerAdjudicatorBallotSetForm, SingleBallotSetForm
from results.models import BallotSubmission, ScoreCriterion
from tournaments.models import Round, Tournament


class BallotSetFormTestMixin:
    """Sets up a two-team debate with one chair, for ballot form tests."""

    def setUp(self):
        self.tournament = Tournament.objects.create(slug="formtest", name="Form Test")
        round = Round.objects.create(
            tournament=self.tournament, seq=1, schedule_group=1, abbreviation="R1",
        )
        self.debate = Debate.objects.create(round=round)
        for side in (DebateSide.AFF, DebateSide.NEG):
            team = Team.objects.create(tournament=self.tournament, reference=f"Team {side}")
            DebateTeam.objects.create(debate=self.debate, team=team, side=side)

        self.adjudicator = Adjudicator.objects.create(
            tournament=self.tournament, name="Chair", base_score=5,
        )
        DebateAdjudicator.objects.create(
            debate=self.debate,
            adjudicator=self.adjudicator,
            type=DebateAdjudicator.TYPE_CHAIR,
        )
        self.ballotsub = BallotSubmission(debate=self.debate)

    def create_criterion(self, **kwargs):
        return ScoreCriterion.objects.create(tournament=self.tournament, **{
            'name': "Content", 'seq': 1, 'weight': 1,
            'min_score': 0, 'max_score': 100, 'step': 1,
            **kwargs,
        })

    def assertIsDerivedTotalField(self, field):
        """The total for a position with criteria is computed from its criterion
        fields, so it is display-only and must not carry the tournament's
        score_min/score_max validators."""
        self.assertNotIsInstance(field, forms.FloatField)
        self.assertTrue(field.widget.attrs.get('readonly'))
        self.assertEqual(0, field.clean(0))  # below score_min, but not validated


class PerAdjudicatorBallotSetFormTests(BallotSetFormTestMixin, TestCase):

    def test_derived_criterion_total_does_not_validate_score_range(self):
        self.create_criterion()

        form = PerAdjudicatorBallotSetForm(
            self.ballotsub, tabroom=True, filled=True, vetos={},
        )
        field_name = form._fieldname_score(self.adjudicator, DebateSide.AFF, 1)
        self.assertIsDerivedTotalField(form.fields[field_name])

    def test_entered_speaker_score_still_validates_score_range(self):
        form = PerAdjudicatorBallotSetForm(self.ballotsub, tabroom=True)
        field_name = form._fieldname_score(self.adjudicator, DebateSide.AFF, 1)

        with self.assertRaises(forms.ValidationError):
            form.fields[field_name].clean(0)


class SingleBallotSetFormTests(BallotSetFormTestMixin, TestCase):

    def test_derived_criterion_total_does_not_validate_score_range(self):
        self.create_criterion()

        form = SingleBallotSetForm(self.ballotsub, tabroom=True, filled=True, vetos={})
        field_name = form._fieldname_score(DebateSide.AFF, 1)
        self.assertIsDerivedTotalField(form.fields[field_name])

    def test_entered_speaker_score_still_validates_score_range(self):
        form = SingleBallotSetForm(self.ballotsub, tabroom=True)
        field_name = form._fieldname_score(DebateSide.AFF, 1)

        with self.assertRaises(forms.ValidationError):
            form.fields[field_name].clean(0)

    def test_reply_only_criterion_leaves_substantive_total_editable(self):
        """The fork scopes criteria per position, so a reply-only criterion must
        not turn substantive totals into derived fields."""
        self.tournament.preferences['debate_rules__reply_scores_enabled'] = True
        self.create_criterion(speech_type=ScoreCriterion.SpeechType.REPLY)

        form = SingleBallotSetForm(self.ballotsub, tabroom=True)
        substantive = form.fields[form._fieldname_score(DebateSide.AFF, 1)]
        reply = form.fields[form._fieldname_score(DebateSide.AFF, form.reply_position)]

        self.assertFalse(substantive.widget.attrs.get('readonly'))
        self.assertIsDerivedTotalField(reply)
