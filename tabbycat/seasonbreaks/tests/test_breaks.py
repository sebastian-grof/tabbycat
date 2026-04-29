from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tournaments.models import Tournament

from ..models import (
    BreakRegion,
    BreakSeason,
    BreakSpeaker,
    BreakSpeakerTournamentParticipation,
    BreakTeam,
    BreakTeamTournamentResult,
    BreakTournament,
    BreaksPermission,
    GlobalBreaksPermission,
)
from ..services import calculate_rankings, calculate_region_quotas


class BreaksPermissionTests(TestCase):
    def test_breaks_index_requires_global_permission(self):
        user = get_user_model().objects.create_user(username='tab', password='pw')
        self.client.login(username='tab', password='pw')
        response = self.client.get(reverse('seasonbreaks-index'))
        self.assertEqual(response.status_code, 403)

        GlobalBreaksPermission.objects.create(user=user, permission=BreaksPermission.VIEW)
        response = self.client.get(reverse('seasonbreaks-index'))
        self.assertEqual(response.status_code, 200)


class BreaksCalculationTests(TestCase):
    def setUp(self):
        self.season = BreakSeason.objects.create(
            name='SDL 2025/26', slug='sdl-2025', league=BreakSeason.League.SDL,
            regional_slots=3, invited_teams=1,
        )
        self.west = BreakRegion.objects.create(season=self.season, name='West', seq=1)
        self.east = BreakRegion.objects.create(season=self.season, name='East', seq=2)
        self.tournament_w1 = Tournament.objects.create(name='West 1', short_name='W1', slug='w1')
        self.tournament_w2 = Tournament.objects.create(name='West 2', short_name='W2', slug='w2')
        self.tournament_e1 = Tournament.objects.create(name='East 1', short_name='E1', slug='e1')
        self.tournament_open = Tournament.objects.create(name='Open', short_name='Open', slug='open')
        self.bt_w1 = BreakTournament.objects.create(season=self.season, tournament=self.tournament_w1, region=self.west, seq=1)
        self.bt_w2 = BreakTournament.objects.create(season=self.season, tournament=self.tournament_w2, region=self.west, seq=2)
        self.bt_e1 = BreakTournament.objects.create(season=self.season, tournament=self.tournament_e1, region=self.east, seq=3)
        self.bt_open = BreakTournament.objects.create(
            season=self.season, tournament=self.tournament_open, region=self.west, seq=4, counts_for_break=False,
        )

    def _team_with_members(self, name, region, tournaments, results):
        team = BreakTeam.objects.create(season=self.season, name=name, region=region)
        for speaker_index in range(2):
            speaker = BreakSpeaker.objects.create(season=self.season, name=f'{name} speaker {speaker_index}')
            for break_tournament in tournaments:
                BreakSpeakerTournamentParticipation.objects.create(
                    break_tournament=break_tournament, break_speaker=speaker,
                    break_team=team, speeches=2, rounds=2,
                )
        for break_tournament, wins, ballots, speaks in results:
            BreakTeamTournamentResult.objects.create(
                break_tournament=break_tournament, break_team=team,
                wins=wins, ballots=ballots, speaker_score=speaks,
                rounds_debated=3, majority_debated=True,
            )
        return team

    def test_quotas_use_largest_remainder_and_odd_invites_add_slot(self):
        self._team_with_members('West A', self.west, [self.bt_w1, self.bt_w2], [(self.bt_w1, 2, 6, 600), (self.bt_w2, 2, 6, 610)])
        self._team_with_members('West B', self.west, [self.bt_w1], [(self.bt_w1, 1, 3, 500)])
        self._team_with_members('East A', self.east, [self.bt_e1], [(self.bt_e1, 1, 3, 500)])

        quotas = {row.region.name: row.allocated for row in calculate_region_quotas(self.season)}
        self.assertEqual(sum(quotas.values()), 4)
        self.assertEqual(quotas['West'], 3)
        self.assertEqual(quotas['East'], 1)

    def test_rankings_use_best_n_minus_one_results_and_member_eligibility(self):
        strong = self._team_with_members('Strong', self.west, [self.bt_w1, self.bt_w2], [
            (self.bt_w1, 1, 3, 500),
            (self.bt_w2, 3, 9, 700),
        ])
        weaker = self._team_with_members('Weaker', self.west, [self.bt_w1, self.bt_w2], [
            (self.bt_w1, 2, 6, 620),
            (self.bt_w2, 2, 6, 610),
        ])

        rankings = calculate_rankings(self.season)[self.west.id]
        self.assertEqual(rankings[0]['team'], strong)
        self.assertEqual(rankings[0]['wins'], 3)
        self.assertTrue(rankings[0]['eligible'])
        self.assertEqual(rankings[0]['eligible_speakers'], ['Strong speaker 0', 'Strong speaker 1'])
        self.assertEqual(rankings[1]['team'], weaker)

    def test_nonleague_tournaments_do_not_affect_quotas_or_rankings(self):
        team = self._team_with_members('West A', self.west, [self.bt_w1, self.bt_open], [
            (self.bt_w1, 1, 3, 500),
            (self.bt_open, 99, 99, 9999),
        ])
        BreakTeamTournamentResult.objects.create(
            break_tournament=self.bt_w2, break_team=team, wins=1, ballots=3,
            speaker_score=500, rounds_debated=3, majority_debated=True,
        )

        quotas = {row.region.name: row.participations for row in calculate_region_quotas(self.season)}
        rankings = calculate_rankings(self.season)[self.west.id]

        self.assertEqual(quotas['West'], 2)
        self.assertEqual(rankings[0]['wins'], 1)
        self.assertEqual(rankings[0]['participations'], 2)
        self.assertEqual(rankings[0]['required_tournaments'], 1)
