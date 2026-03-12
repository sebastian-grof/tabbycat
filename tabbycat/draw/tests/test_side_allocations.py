from django.test import TestCase

from availability.utils import set_availability
from utils.tests import AdminTournamentViewSimpleLoadTestMixin, CompletedTournamentTestMixin

from ..manager import DrawManager
from ..side_allocations import generate_opposite_allocations, generate_random_allocations, replace_round_allocations


class SideAllocationsViewTest(AdminTournamentViewSimpleLoadTestMixin, TestCase):
    view_name = 'draw-side-allocations'


class SideAllocationServiceTest(CompletedTournamentTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.round1 = self.tournament.round_set.get(seq=1)
        self.round2 = self.tournament.round_set.get(seq=2)
        self.sides = list(self.tournament.sides)

    def test_generate_random_allocations(self):
        allocations = generate_random_allocations(self.round1)

        self.assertEqual(len(allocations), self.tournament.team_set.count())
        self.assertEqual(
            sum(1 for side in allocations.values() if side == self.sides[0]),
            sum(1 for side in allocations.values() if side == self.sides[1]),
        )
        self.assertEqual(self.round1.teamsideallocation_set.count(), self.tournament.team_set.count())

    def test_generate_opposite_allocations(self):
        source_allocations = generate_random_allocations(self.round1)
        target_allocations = generate_opposite_allocations(self.round2, self.round1)

        opposite_side = {self.sides[0]: self.sides[1], self.sides[1]: self.sides[0]}
        for team_id, side in source_allocations.items():
            self.assertEqual(target_allocations[team_id], opposite_side[side])

    def test_generate_opposite_allocations_fills_missing_source_team(self):
        teams = list(self.tournament.team_set.order_by('id'))
        missing_team = teams[0]
        source_allocations = {}
        for team in teams[1:12]:
            source_allocations[team.id] = self.sides[0]
        for team in teams[12:]:
            source_allocations[team.id] = self.sides[1]
        replace_round_allocations(self.round1, source_allocations)

        target_allocations = generate_opposite_allocations(self.round2, self.round1)

        self.assertEqual(len(target_allocations), len(teams))
        self.assertIn(missing_team.id, target_allocations)
        self.assertEqual(
            sum(1 for side in target_allocations.values() if side == self.sides[0]),
            sum(1 for side in target_allocations.values() if side == self.sides[1]),
        )

    def test_generate_random_allocations_uses_only_debating_teams(self):
        available_teams = self.tournament.team_set.order_by('id')[:23]
        set_availability(available_teams, self.round1)
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'

        allocations = generate_random_allocations(self.round1)
        draw_teams, byes = DrawManager(self.round1).get_teams()

        self.assertEqual(len(byes), 1)
        self.assertEqual(len(allocations), len(draw_teams))
        self.assertEqual(set(allocations.keys()), {team.id for team in draw_teams})
        self.assertNotIn(byes[0].id, allocations)

    def test_preallocated_unassigned_active_team_becomes_bye(self):
        available_teams = list(self.tournament.team_set.order_by('id')[:23])
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in available_teams]), self.round1)
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'

        chosen_bye = available_teams[0]
        debating_teams = [team for team in available_teams if team.id != chosen_bye.id]
        allocations = {}
        halfway = len(debating_teams) // 2
        for team in debating_teams[:halfway]:
            allocations[team.id] = self.sides[0]
        for team in debating_teams[halfway:]:
            allocations[team.id] = self.sides[1]
        replace_round_allocations(self.round1, allocations)

        draw_teams, byes = DrawManager(self.round1).get_teams()

        self.assertEqual([team.id for team in byes], [chosen_bye.id])
        self.assertNotIn(chosen_bye.id, {team.id for team in draw_teams})
