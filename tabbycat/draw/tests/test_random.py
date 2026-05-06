from availability.utils import activate_all
from draw.manager import DrawManager
from draw.models import DebateTeam
from draw.side_allocations import generate_random_allocations
from draw.types import DebateSide
from participants.models import Team
from tournaments.models import Round
from utils.tests import BaseMinimalTournamentTestCase


class RandomDrawTests(BaseMinimalTournamentTestCase):

    def setUp(self):
        super(RandomDrawTests, self).setUp()
        self.round = Round(tournament=self.tournament, seq=2, draw_type=Round.DrawType.RANDOM)
        self.round.save()
        activate_all(self.round)

    def test_std(self):
        DrawManager(self.round).create()

        self.assertEqual(6, self.round.debate_set.count())
        self.assertEqual(12, DebateTeam.objects.filter(debate__round=self.round).count())

        for team in Team.objects.all():
            self.assertEqual(1, DebateTeam.objects.filter(team=team).count())

    def test_solo_random_draw_creates_one_debate_per_team(self):
        self.tournament.preferences['debate_rules__teams_in_debate'] = 1
        self.tournament.preferences['debate_rules__solo_speech_format'] = True
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'off'
        self.tournament._prefs.clear()

        allocations = generate_random_allocations(self.round)

        DrawManager(self.round).create()

        self.assertEqual(12, self.round.debate_set.count())
        self.assertEqual(12, DebateTeam.objects.filter(debate__round=self.round).count())
        self.assertEqual(0, DebateTeam.objects.filter(debate__round=self.round, side=DebateSide.BYE).count())
        self.assertEqual(6, sum(1 for side in allocations.values() if side == DebateSide.AFF))
        self.assertEqual(6, sum(1 for side in allocations.values() if side == DebateSide.NEG))

        for debate in self.round.debate_set.all():
            self.assertEqual(1, debate.debateteam_set.count())
