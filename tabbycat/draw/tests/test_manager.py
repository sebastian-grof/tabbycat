import unittest
from types import SimpleNamespace

from ..manager import RandomDrawManager
from ..generator.pairing import Pairing
from ..side_allocation_pairings import apply_postallocated_sides
from ..tests.utils import TestTeam
from ..types import DebateSide


class PostAllocatedSidesTest(unittest.TestCase):

    def setUp(self):
        tournament = SimpleNamespace(
            sides=[DebateSide.AFF, DebateSide.NEG],
            pref=lambda name: {
                "side_names": "aff-neg",
                "teams_in_debate": 2,
            }[name],
        )
        round = SimpleNamespace(
            name="Round 5",
            tournament=tournament,
            teamsideallocation_set=SimpleNamespace(all=lambda: []),
        )
        self.round = round

    def set_allocations(self, mapping):
        allocations = [
            SimpleNamespace(team_id=team_id, side=side)
            for team_id, side in mapping.items()
        ]
        self.round.teamsideallocation_set = SimpleNamespace(all=lambda: allocations)

    def test_apply_postallocated_sides_reverses_pairing(self):
        team1 = TestTeam(1, "A")
        team2 = TestTeam(2, "B")
        pairing = Pairing(teams=[team1, team2], bracket=0, room_rank=1)
        self.set_allocations({
            team1.id: DebateSide.NEG,
            team2.id: DebateSide.AFF,
        })

        apply_postallocated_sides(self.round, [pairing])

        self.assertEqual(pairing.teams, [team2, team1])


class RandomDrawByeFallbackTest(unittest.TestCase):

    def setUp(self):
        tournament = SimpleNamespace(
            sides=[DebateSide.AFF, DebateSide.NEG],
            pref=lambda name: {
                "teams_in_debate": 2,
                "bye_team_selection": "middle_odd_bracket",
            }[name],
            preferences={},
        )
        self.round = SimpleNamespace(
            tournament=tournament,
            draw_type="random",
        )

    def test_middle_odd_bracket_falls_back_to_random_bye_for_random_draws(self):
        teams = [
            TestTeam(1, "A"),
            TestTeam(2, "B"),
            TestTeam(3, "C"),
        ]
        manager = RandomDrawManager(self.round)

        debating_teams, byes = manager._special_bye_selection(teams, 1)

        self.assertEqual(len(debating_teams), 2)
        self.assertEqual(len(byes), 1)
        self.assertCountEqual(debating_teams + byes, teams)

    def test_apply_postallocated_sides_balances_same_side_conflict(self):
        team1 = TestTeam(1, "A", side_history=[2, 0])
        team2 = TestTeam(2, "B", side_history=[0, 2])
        pairing = Pairing(teams=[team1, team2], bracket=0, room_rank=1)
        self.set_allocations({
            team1.id: DebateSide.AFF,
            team2.id: DebateSide.AFF,
        })

        apply_postallocated_sides(self.round, [pairing])

        self.assertEqual(pairing.teams, [team2, team1])
