from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from availability.utils import set_availability
from participants.models import Team
from results.models import TeamScore
from standings.base import StandingsError
from tournaments.models import Round
from utils.misc import add_query_string_parameter, reverse_tournament
from utils.tests import CompletedTournamentTestMixin

from ..models import ByeTeamOverride, TeamSideAllocation
from ..side_allocation_display import get_team_navigation


class SideAllocationDisplayTest(CompletedTournamentTestMixin, TestCase):

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        super().setUp()
        self.round1 = self.tournament.round_set.get(seq=1)
        self.round2 = self.tournament.round_set.get(seq=2)
        self.teams = list(self.tournament.team_set.order_by("short_name", "id"))
        self.tournament.preferences['standings__team_standings_precedence'] = ['points', 'speaks_sum']

    def navigation(self, round=None):
        return get_team_navigation(self.tournament, round or self.round2, self.teams)

    def test_first_round_never_includes_later_results(self):
        with patch('draw.side_allocation_display.TeamStandingsGenerator') as generator:
            navigation = self.navigation(self.round1)
        generator.assert_not_called()
        self.assertFalse(navigation['available'])
        self.assertIn('No prior results', navigation['context'])
        self.assertTrue(all(team['rank'] is None for team in navigation['teams']))
        self.assertTrue(all(team['statistics'] == {'wins': 0, 'ballots': 0, 'team_points': 0} for team in navigation['teams']))

    def test_team_statistics_use_confirmed_prior_results(self):
        scores = TeamScore.objects.filter(debate_team__debate__round=self.round1, ballot_submission__confirmed=True)
        scores.update(win=True, score=210, votes_given=2, votes_possible=3)
        by_id = {team['id']: team for team in self.navigation()['teams']}
        self.assertEqual(by_id[self.teams[0].id]['statistics'], {'wins': 1, 'ballots': 2, 'team_points': 210})
        ballot = scores.filter(debate_team__team=self.teams[0]).first().ballot_submission
        ballot.confirmed = False
        ballot.save(update_fields=['confirmed'])
        by_id = {team['id']: team for team in self.navigation()['teams']}
        self.assertEqual(by_id[self.teams[0].id]['statistics'], {'wins': 0, 'ballots': 0, 'team_points': 0})

    def test_selected_and_later_results_do_not_change_navigation(self):
        before = self.navigation()
        self.assertTrue(before['available'])
        self.assertIn(self.round1.name, before['context'])
        TeamScore.objects.filter(debate_team__debate__round__seq__gte=self.round2.seq).update(points=50, score=1000)
        self.assertEqual(self.navigation(), before)

    def test_primary_metric_defines_brackets_and_ties_share_ranks(self):
        scores = TeamScore.objects.filter(debate_team__debate__round=self.round1, ballot_submission__confirmed=True)
        scores.update(points=1, score=70)
        scores.filter(debate_team__team=self.teams[0]).update(points=2, score=60)
        navigation = self.navigation()
        by_id = {team['id']: team for team in navigation['teams']}
        self.assertEqual(by_id[self.teams[0].id]['rank'], 1)
        self.assertEqual(by_id[self.teams[0].id]['bracketOrder'], 0)
        self.assertEqual(by_id[self.teams[1].id]['rank'], by_id[self.teams[2].id]['rank'])
        self.assertEqual(by_id[self.teams[1].id]['bracketOrder'], 1)
        self.assertIn('2', by_id[self.teams[0].id]['bracketLabel'])
        self.assertEqual(self.navigation(), navigation)

    def test_configured_precedence_can_use_a_different_primary_metric(self):
        scores = TeamScore.objects.filter(debate_team__debate__round=self.round1, ballot_submission__confirmed=True)
        scores.update(points=1, score=70)
        scores.filter(debate_team__team=self.teams[0]).update(points=2, score=60)
        self.tournament.preferences['standings__team_standings_precedence'] = ['speaks_sum', 'points']
        by_id = {team['id']: team for team in self.navigation()['teams']}
        self.assertGreater(by_id[self.teams[0].id]['rank'], by_id[self.teams[1].id]['rank'])
        self.assertGreater(by_id[self.teams[0].id]['bracketOrder'], by_id[self.teams[1].id]['bracketOrder'])

    def test_no_confirmed_results_falls_back(self):
        TeamScore.objects.filter(debate_team__debate__round=self.round1).delete()
        self.assertFalse(self.navigation()['available'])

    def test_placeholder_bye_team_stays_visible_but_is_not_ranked(self):
        self.tournament.team_set.filter(id=self.teams[0].id).update(type=Team.TYPE_BYE)
        navigation = self.navigation()
        self.assertEqual(len(navigation['teams']), len(self.teams))
        self.assertIsNone(next(team['rank'] for team in navigation['teams'] if team['id'] == self.teams[0].id))

    def test_missing_standings_configuration_falls_back(self):
        self.tournament.preferences['standings__team_standings_precedence'] = []
        self.assertIn('No standings metrics', self.navigation()['context'])

    def test_invalid_standings_configuration_falls_back(self):
        with patch('draw.side_allocation_display.TeamStandingsGenerator', side_effect=StandingsError('Invalid metric')):
            navigation = self.navigation()
        self.assertFalse(navigation['available'])
        self.assertIn('Standings unavailable', navigation['context'])

    def test_editor_labels_and_forms_preserve_all_active_teams(self):
        set_availability(self.tournament.team_set.all(), self.round2)
        user = get_user_model().objects.create(username='side_editor', is_superuser=True)
        self.client.force_login(user)
        url = add_query_string_parameter(reverse_tournament('draw-side-allocations', self.tournament), 'round_seq', self.round2.seq)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-team-table="manual"')
        self.assertContains(response, 'data-team-table="overview"')
        self.assertContains(response, 'data-apply-sort')
        for metric in ['wins', 'ballots', 'team-points']:
            self.assertContains(response, f'data-team-statistic="{metric}"', count=len(self.teams))
        self.assertContains(response, 'data-rank-value', count=len(self.teams))
        self.assertLess(response.content.index(b'id="saved-allocation-heading"'), response.content.index(b'Round workspace'))
        for team in self.teams:
            self.assertContains(response, f'for="id_manual-team_{team.id}"')
        self.assertEqual({team['id'] for team in response.context['team_navigation']['teams']}, {team.id for team in self.teams})
        data = {'action': 'manual', 'manual-selected_round': self.round2.id}
        data.update({f'manual-team_{team.id}': str(self.tournament.sides[index % 2]) for index, team in enumerate(self.teams)})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TeamSideAllocation.objects.filter(round=self.round2).count(), len(self.teams))


class SideAllocationWorkspaceTest(CompletedTournamentTestMixin, TestCase):

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        super().setUp()
        self.round1 = self.tournament.round_set.get(seq=1)
        self.round2 = self.tournament.round_set.get(seq=2)
        self.tournament.round_set.filter(id__in=[self.round1.id, self.round2.id]).update(draw_type=Round.DrawType.RANDOM)
        set_availability(self.tournament.team_set.all(), self.round1)
        set_availability(self.tournament.team_set.all(), self.round2)
        user = get_user_model().objects.create(username='workspace_editor', is_superuser=True)
        self.client.force_login(user)
        self.url = add_query_string_parameter(reverse_tournament('draw-side-allocations', self.tournament), 'round_seq', self.round2.seq)

    def test_all_generation_modes_keep_their_existing_results(self):
        for mode in ['random', 'all_aff', 'all_neg', 'opposite', 'clear']:
            with self.subTest(mode=mode):
                response = self.client.post(self.url, {
                    'action': 'generate',
                    'generate-target_round': self.round2.id,
                    'generate-mode': mode,
                    'generate-source_round': self.round1.id,
                })
                self.assertRedirects(response, self.url)
                allocations = TeamSideAllocation.objects.filter(round=self.round2)
                self.assertEqual(allocations.count(), 0 if mode == 'clear' else self.tournament.team_set.count())
                if mode in ['all_aff', 'all_neg']:
                    expected_side = self.tournament.sides[0 if mode == 'all_aff' else 1]
                    self.assertEqual(set(allocations.values_list('side', flat=True)), {expected_side})

    def test_invalid_generation_keeps_bound_values_and_error_visible(self):
        response = self.client.post(self.url, {
            'action': 'generate',
            'generate-target_round': self.round2.id,
            'generate-mode': 'opposite',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['generate_form']['source_round'].errors)
        self.assertContains(response, '<option value="opposite" selected>Opposite of round</option>')

    def test_invalid_manual_choice_preserves_other_edits(self):
        teams = list(self.tournament.team_set.all())
        values = {f'manual-team_{team.id}': str(self.tournament.sides[0]) for team in teams}
        values[f'manual-team_{teams[0].id}'] = 'invalid-side'
        response = self.client.post(self.url, {'action': 'manual', 'manual-selected_round': self.round2.id, **values})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['manual_form'][f'team_{teams[0].id}'].errors)
        self.assertEqual(response.context['manual_form'][f'team_{teams[1].id}'].value(), str(self.tournament.sides[0]))
        self.assertFalse(TeamSideAllocation.objects.filter(round=self.round2).exists())

    def test_empty_editor_keeps_full_overview(self):
        set_availability(self.tournament.team_set.none(), self.round2)
        response = self.client.get(self.url)
        self.assertContains(response, 'There are no debating teams available')
        self.assertEqual(len(response.context['allocation_rows']), self.tournament.team_set.count())

    def test_bye_override_can_be_set_and_cleared(self):
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'random'
        teams = self.tournament.team_set.order_by('id')[:23]
        set_availability(teams, self.round2)
        team = teams.first()
        response = self.client.post(self.url, {'action': 'bye', 'bye-selected_round': self.round2.id, 'bye-team': team.id})
        self.assertRedirects(response, self.url)
        self.assertEqual(ByeTeamOverride.objects.get(round=self.round2).team_id, team.id)
        response = self.client.post(self.url, {'action': 'bye', 'bye-selected_round': self.round2.id, 'bye-team': ''})
        self.assertRedirects(response, self.url)
        self.assertFalse(ByeTeamOverride.objects.filter(round=self.round2).exists())

    def test_no_preliminary_rounds_keeps_empty_state(self):
        self.tournament.round_set.update(stage=Round.Stage.ELIMINATION)
        response = self.client.get(self.url)
        self.assertContains(response, 'There are no preliminary rounds to edit yet.')
        self.assertFalse(response.context['team_navigation']['available'])

    def test_other_formats_keep_warning_and_overview(self):
        self.tournament.preferences['debate_rules__teams_in_debate'] = 4
        response = self.client.get(self.url)
        self.assertContains(response, 'These tools are designed for two-team formats.')
        self.assertEqual(len(response.context['allocation_rows']), self.tournament.team_set.count())
