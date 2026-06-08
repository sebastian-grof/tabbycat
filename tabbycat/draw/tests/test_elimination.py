from collections import Counter

from django.test import TestCase

from breakqual.models import BreakCategory, BreakingTeam
from draw.manager import DrawManager
from draw.models import DebateTeam, TeamSideAllocation
from draw.types import DebateSide
from participants.models import Institution, Speaker, Team
from tournaments.models import Round, Tournament


class SoloEliminationDrawTests(TestCase):

    def setUp(self):
        super().setUp()
        self.tournament = Tournament.objects.create(slug="tournament")
        institution = Institution.objects.create(code="INS", name="Institution")
        for i in range(3):
            team = Team.objects.create(
                tournament=self.tournament,
                institution=institution,
                reference="Team%s" % i,
            )
            Speaker.objects.create(team=team, name="Speaker%s" % i)

        self.tournament.preferences['debate_rules__teams_in_debate'] = 1
        self.tournament.preferences['debate_rules__solo_speech_format'] = True
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'off'
        self.tournament._prefs.clear()

        self.category = BreakCategory.objects.create(
            tournament=self.tournament,
            name="Open",
            slug="open",
            seq=1,
            break_size=3,
            is_general=True,
            priority=1,
        )
        self.round = Round.objects.create(
            tournament=self.tournament,
            seq=1,
            name="Grand Final",
            abbreviation="GF",
            stage=Round.Stage.ELIMINATION,
            draw_type=Round.DrawType.ELIMINATION,
            break_category=self.category,
        )
        self.breaking_teams = list(self.tournament.team_set.order_by("id")[:3])
        for rank, team in enumerate(self.breaking_teams, start=1):
            BreakingTeam.objects.create(
                break_category=self.category,
                team=team,
                rank=rank,
                break_rank=rank,
            )

    def test_solo_break_size_creates_one_break_round(self):
        self.assertEqual(1, self.category.num_break_rounds)

    def test_solo_elimination_draw_creates_one_debate_per_breaking_team(self):
        debates = DrawManager(self.round).create()
        self.round.refresh_from_db()

        self.assertEqual(Round.Status.DRAFT, self.round.draw_status)
        self.assertEqual(3, len(debates))
        self.assertEqual(3, self.round.debate_set.count())
        self.assertEqual(3, DebateTeam.objects.filter(debate__round=self.round).count())
        self.assertEqual(3, TeamSideAllocation.objects.filter(round=self.round).count())

        debate_teams = list(DebateTeam.objects.filter(debate__round=self.round).select_related("team"))
        self.assertCountEqual([dt.team for dt in debate_teams], self.breaking_teams)
        self.assertEqual([1, 2], sorted(Counter(dt.side for dt in debate_teams).values()))

        for debate in self.round.debate_set.all():
            self.assertEqual(1, debate.debateteam_set.count())

    def test_solo_elimination_draw_preserves_saved_side_allocations(self):
        TeamSideAllocation.objects.create(
            round=self.round,
            team=self.breaking_teams[0],
            side=DebateSide.NEG,
        )

        DrawManager(self.round).create()

        debate_team = DebateTeam.objects.get(debate__round=self.round, team=self.breaking_teams[0])
        self.assertEqual(DebateSide.NEG, debate_team.side)
