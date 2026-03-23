from django.contrib.auth import get_user_model
from django.test import TestCase

from availability.utils import set_availability
from tournaments.models import Round
from utils.misc import add_query_string_parameter, reverse_tournament
from utils.tests import AdminTournamentViewSimpleLoadTestMixin, CompletedTournamentTestMixin

from ..manager import DrawManager
from ..models import ByeTeamOverride, Debate, DebateTeam, get_effective_side_allocation_mode
from ..side_allocations import generate_opposite_allocations, generate_random_allocations, replace_round_allocations
from ..types import DebateSide


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

    def test_generate_random_allocations_assigns_all_active_teams_when_bye_is_automatic(self):
        available_teams = self.tournament.team_set.order_by('id')[:23]
        set_availability(available_teams, self.round2)
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'middle_odd_bracket'
        self.tournament.preferences['draw_rules__draw_odd_bracket'] = 'pullup_top'
        self.tournament.preferences['draw_rules__draw_pairing_method'] = 'fold'

        allocations = generate_random_allocations(self.round2)
        draw_teams, byes = DrawManager(self.round2).get_teams()

        self.assertEqual(len(byes), 1)
        self.assertEqual(len(allocations), len(available_teams))
        self.assertEqual(set(allocations.keys()), {team.id for team in available_teams})
        self.assertIn(byes[0].id, allocations)

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

    def test_manual_bye_override_takes_precedence_over_random_selection(self):
        available_teams = list(self.tournament.team_set.order_by('id')[:23])
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in available_teams]), self.round1)
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'random'

        chosen_bye = available_teams[5]
        ByeTeamOverride.objects.create(round=self.round1, team=chosen_bye)

        draw_teams, byes = DrawManager(self.round1).get_teams()

        self.assertEqual([team.id for team in byes], [chosen_bye.id])
        self.assertNotIn(chosen_bye.id, {team.id for team in draw_teams})

    def test_generate_random_allocations_respects_manual_bye_override(self):
        available_teams = list(self.tournament.team_set.order_by('id')[:23])
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in available_teams]), self.round1)
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'random'

        chosen_bye = available_teams[7]
        ByeTeamOverride.objects.create(round=self.round1, team=chosen_bye)

        allocations = generate_random_allocations(self.round1)
        draw_teams, byes = DrawManager(self.round1).get_teams()

        self.assertEqual(len(byes), 1)
        self.assertEqual([team.id for team in byes], [chosen_bye.id])
        self.assertEqual(len(allocations), len(draw_teams))
        self.assertNotIn(chosen_bye.id, allocations)

    def test_generate_opposite_allocations_assigns_all_active_teams_when_bye_is_automatic(self):
        available_teams = list(self.tournament.team_set.order_by('id')[:23])
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in available_teams]), self.round1)
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in available_teams]), self.round2)
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'middle_odd_bracket'
        self.tournament.preferences['draw_rules__draw_odd_bracket'] = 'pullup_top'
        self.tournament.preferences['draw_rules__draw_pairing_method'] = 'fold'

        source_allocations = {}
        for team in available_teams[:12]:
            source_allocations[team.id] = self.sides[0]
        for team in available_teams[12:]:
            source_allocations[team.id] = self.sides[1]
        replace_round_allocations(self.round1, source_allocations)

        target_allocations = generate_opposite_allocations(self.round2, self.round1)
        draw_teams, byes = DrawManager(self.round2).get_teams()

        self.assertEqual(len(byes), 1)
        self.assertEqual(len(target_allocations), len(available_teams))
        self.assertEqual(set(target_allocations.keys()), {team.id for team in available_teams})
        self.assertIn(byes[0].id, target_allocations)

    def test_generate_opposite_allocations_ignores_source_round_bye_team_side(self):
        source_round = Round.objects.create(tournament=self.tournament, seq=98, abbreviation='RS')
        target_round = Round.objects.create(tournament=self.tournament, seq=99, abbreviation='RT')
        teams = list(self.tournament.team_set.order_by('id')[:5])
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in teams]), source_round)
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in teams]), target_round)

        debate_one = Debate.objects.create(round=source_round, bracket=2, room_rank=1)
        DebateTeam.objects.create(debate=debate_one, team=teams[0], side=DebateSide.AFF)
        DebateTeam.objects.create(debate=debate_one, team=teams[1], side=DebateSide.NEG)

        debate_two = Debate.objects.create(round=source_round, bracket=1, room_rank=2)
        DebateTeam.objects.create(debate=debate_two, team=teams[2], side=DebateSide.AFF)
        DebateTeam.objects.create(debate=debate_two, team=teams[3], side=DebateSide.NEG)

        bye_debate = Debate.objects.create(round=source_round, bracket=0, room_rank=3)
        DebateTeam.objects.create(debate=bye_debate, team=teams[4], side=DebateSide.BYE)

        base_allocations = {
            teams[0].id: self.sides[0],
            teams[1].id: self.sides[1],
            teams[2].id: self.sides[0],
            teams[3].id: self.sides[1],
            teams[4].id: self.sides[0],
        }
        replace_round_allocations(source_round, base_allocations)

        import random
        random.seed(17)
        first = generate_opposite_allocations(target_round, source_round)

        replace_round_allocations(target_round, {})
        base_allocations[teams[4].id] = self.sides[1]
        replace_round_allocations(source_round, base_allocations)

        random.seed(17)
        second = generate_opposite_allocations(target_round, source_round)

        self.assertEqual(first, second)

    def test_round_without_active_allocations_uses_postallocated_mode(self):
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'

        self.assertEqual(get_effective_side_allocation_mode(self.round1), 'postallocated')

    def test_round_with_active_allocations_uses_preallocated_mode(self):
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'
        allocations = {team.id: self.sides[index % 2] for index, team in enumerate(self.tournament.team_set.order_by('id')[:4])}
        replace_round_allocations(self.round1, allocations)

        self.assertEqual(get_effective_side_allocation_mode(self.round1), 'preallocated')

    def test_middle_odd_bracket_works_with_active_preallocations(self):
        available_teams = list(self.tournament.team_set.order_by('id')[:23])
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in available_teams]), self.round2)
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'middle_odd_bracket'
        self.tournament.preferences['draw_rules__draw_odd_bracket'] = 'pullup_top'
        self.tournament.preferences['draw_rules__draw_pairing_method'] = 'fold'
        self.tournament.preferences['draw_rules__draw_avoid_conflicts'] = 'one_up_one_down'

        allocations = {}
        for team in available_teams[:12]:
            allocations[team.id] = self.sides[0]
        for team in available_teams[12:]:
            allocations[team.id] = self.sides[1]
        replace_round_allocations(self.round2, allocations)

        draw_teams, byes = DrawManager(self.round2).get_teams()

        self.assertEqual(len(byes), 1)
        self.assertEqual(len(draw_teams), 22)
        self.assertNotIn(byes[0].id, {team.id for team in draw_teams})

    def test_legacy_unmatched_team_value_maps_to_final_odd_bracket_selection(self):
        available_teams = list(self.tournament.team_set.order_by('id')[:23])
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in available_teams]), self.round2)
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'unmatched_team'
        self.tournament.preferences['draw_rules__draw_avoid_conflicts'] = 'fold_after_pullups'
        self.tournament.preferences['draw_rules__draw_odd_bracket'] = 'pullup_top'
        self.tournament.preferences['draw_rules__draw_pairing_method'] = 'fold'

        draw_teams, byes = DrawManager(self.round2).get_teams()

        self.assertEqual(len(byes), 1)
        self.assertEqual(len(draw_teams), 22)
        self.assertNotIn(byes[0].id, {team.id for team in draw_teams})
        self.assertEqual(self.tournament.preferences['draw_rules__bye_team_selection'], 'middle_odd_bracket')


class SideAllocationByeOverrideViewTest(CompletedTournamentTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.round1 = self.tournament.round_set.get(seq=1)
        user, _ = get_user_model().objects.get_or_create(username='test_admin', is_superuser=True)
        self.client.force_login(user)

    def test_post_sets_bye_override(self):
        available_teams = list(self.tournament.team_set.order_by('id')[:23])
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in available_teams]), self.round1)
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'random'

        chosen_bye = available_teams[3]
        url = add_query_string_parameter(reverse_tournament('draw-side-allocations', self.tournament), 'round_seq', self.round1.seq)

        response = self.client.post(url, {
            'action': 'bye',
            'bye-selected_round': self.round1.id,
            'bye-team': chosen_bye.id,
        })

        self.assertRedirects(response, url)
        self.assertEqual(self.round1.bye_team_override.team_id, chosen_bye.id)

    def test_post_clear_generation_removes_allocations(self):
        self.tournament.preferences['draw_rules__draw_side_allocations'] = 'preallocated'
        allocations = {team.id: self.round1.tournament.sides[index % 2] for index, team in enumerate(self.tournament.team_set.order_by('id')[:4])}
        replace_round_allocations(self.round1, allocations)
        url = add_query_string_parameter(reverse_tournament('draw-side-allocations', self.tournament), 'round_seq', self.round1.seq)

        response = self.client.post(url, {
            'action': 'generate',
            'generate-target_round': self.round1.id,
            'generate-mode': 'clear',
        })

        self.assertRedirects(response, url)
        self.assertEqual(self.round1.teamsideallocation_set.count(), 0)
