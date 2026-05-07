from django.test import TestCase

from adjallocation.models import DebateAdjudicator
from draw.models import Debate, DebateTeam
from draw.types import DebateSide
from options.presets import JDLFirstCategoryPreferences
from participants.models import Adjudicator, Institution, Speaker, Team
from privateurls.views import PersonIndexView
from results.models import BallotSubmission
from results.views import AdjudicatorPrivateUrlBallotScoresheetView, BasePublicNewBallotSetView
from tournaments.models import Round, Tournament
from venues.models import Venue


class JDLMultiSpeechPrivateUrlTests(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug="jdl-multi", name="JDL Multi Speech")
        JDLFirstCategoryPreferences.save(self.tournament)
        self.round = Round.objects.create(tournament=self.tournament, seq=1, name="Round 1", abbreviation="R1")
        self.venue = Venue.objects.create(name="Room A", priority=1)
        self.institution = Institution.objects.create(code="SDA", name="SDA")
        self.adjudicator = Adjudicator.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            name="Anna Judge",
            url_key="anna-judge",
            base_score=5,
        )

        self.debate_one = self._create_solo_debate("Speaker One", DebateSide.AFF)
        self.debate_two = self._create_solo_debate("Speaker Two", DebateSide.NEG)
        self.debate_adj_one = DebateAdjudicator.objects.create(
            debate=self.debate_one,
            adjudicator=self.adjudicator,
            type=DebateAdjudicator.TYPE_CHAIR,
        )
        self.debate_adj_two = DebateAdjudicator.objects.create(
            debate=self.debate_two,
            adjudicator=self.adjudicator,
            type=DebateAdjudicator.TYPE_CHAIR,
        )

    def _create_solo_debate(self, speaker_name, side):
        team = Team.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            reference=speaker_name,
            use_institution_prefix=False,
        )
        Speaker.objects.create(team=team, name=speaker_name)
        debate = Debate.objects.create(round=self.round, venue=self.venue)
        DebateTeam.objects.create(debate=debate, team=team, side=side)
        return debate

    def test_same_adjudicator_can_be_assigned_to_multiple_solo_debates(self):
        self.assertEqual(
            DebateAdjudicator.objects.filter(adjudicator=self.adjudicator, debate__round=self.round).count(),
            2,
        )

    def test_debate_specific_new_ballot_queryset_selects_one_assignment(self):
        view = BasePublicNewBallotSetView()
        view.object = self.adjudicator
        view.round = self.round
        view.kwargs = {'url_key': self.adjudicator.url_key, 'debate_id': self.debate_two.id}

        self.assertEqual(list(view._adjudicator_debate_queryset()), [self.debate_adj_two])

    def test_debate_specific_scoresheet_queryset_selects_one_debate(self):
        view = AdjudicatorPrivateUrlBallotScoresheetView()
        view._tournament_from_url = self.tournament
        view.round = self.round
        view.kwargs = {
            'tournament_slug': self.tournament.slug,
            'round_seq': self.round.seq,
            'url_key': self.adjudicator.url_key,
            'debate_id': self.debate_one.id,
        }

        self.assertEqual(list(view.get_queryset()), [self.debate_one])

    def test_adjudicator_landing_actions_are_debate_specific(self):
        view = PersonIndexView()
        view.object = self.adjudicator
        view._tournament_from_url = self.tournament

        actions = view._adjudicator_ballot_actions([self.debate_adj_one, self.debate_adj_two])

        self.assertEqual(len(actions), 2)
        self.assertNotEqual(actions[0]['url'], actions[1]['url'])
        self.assertIn(str(self.debate_one.id), actions[0]['url'])
        self.assertIn(str(self.debate_two.id), actions[1]['url'])
        self.assertIn("Submit Ballot", actions[0]['text'])
        self.assertEqual(actions[0]['subtext'], "")
        self.assertFalse(actions[0]['to_complete'])
        self.assertEqual(actions[0]['type'], 'primary')

    def test_landing_actions_hide_submitted_ballots(self):
        BallotSubmission.objects.create(
            debate=self.debate_one,
            participant_submitter=self.adjudicator,
            submitter_type=BallotSubmission.Submitter.PUBLIC,
            private_url=True,
            single_adj=True,
        )
        view = PersonIndexView()
        view.object = self.adjudicator
        view._tournament_from_url = self.tournament

        actions = view._adjudicator_ballot_actions([self.debate_adj_one, self.debate_adj_two])

        self.assertEqual(len(actions), 1)
        self.assertIn(str(self.debate_two.id), actions[0]['url'])
        self.assertIn("Submit Ballot", actions[0]['text'])

    def test_landing_actions_ignore_non_chair_allocations(self):
        debate = self._create_solo_debate("Speaker Three", DebateSide.AFF)
        panel_allocation = DebateAdjudicator.objects.create(
            debate=debate,
            adjudicator=self.adjudicator,
            type=DebateAdjudicator.TYPE_PANEL,
        )
        view = PersonIndexView()
        view.object = self.adjudicator
        view._tournament_from_url = self.tournament

        actions = view._adjudicator_ballot_actions([self.debate_adj_one, self.debate_adj_two, panel_allocation])

        self.assertEqual(len(actions), 2)
        self.assertNotIn(str(debate.id), [action['url'] for action in actions])
