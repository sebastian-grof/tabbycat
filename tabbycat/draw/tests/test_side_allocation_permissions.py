from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from availability.utils import set_availability
from tournaments.models import Round, Tournament
from users.models import Group, Membership, UserPermission
from users.permissions import Permission
from utils.misc import add_query_string_parameter, reverse_tournament
from utils.tests import CompletedTournamentTestMixin

from ..models import ByeTeamOverride, TeamSideAllocation


class SideAllocationPermissionTest(CompletedTournamentTestMixin, TestCase):

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        super().setUp()
        self.round = self.tournament.round_set.get(seq=2)
        self.round.draw_type = Round.DrawType.RANDOM
        self.round.save(update_fields=['draw_type'])
        self.tournament.preferences['draw_rules__bye_team_selection'] = 'random'
        self.teams = list(self.tournament.team_set.order_by('id')[:23])
        set_availability(self.tournament.team_set.filter(id__in=[team.id for team in self.teams]), self.round)
        self.user = get_user_model().objects.create_user(username='tournament_side_editor')
        self.client.force_login(self.user)
        self.url = add_query_string_parameter(reverse_tournament('draw-side-allocations', self.tournament), 'round_seq', self.round.seq)
        self.payloads = [
            {'action': 'manual', 'manual-selected_round': self.round.id, **{
                f'manual-team_{team.id}': str(self.tournament.sides[index % 2])
                for index, team in enumerate(self.teams)
            }},
            {'action': 'generate', 'generate-target_round': self.round.id, 'generate-mode': 'random'},
            {'action': 'bye', 'bye-selected_round': self.round.id, 'bye-team': self.teams[0].id},
        ]

    def assert_actions_allowed(self):
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for data in self.payloads:
            with self.subTest(action=data['action']):
                self.assertRedirects(self.client.post(self.url, data), self.url, fetch_redirect_response=False)
        self.assertTrue(response.context['can_edit'])
        self.assertEqual(TeamSideAllocation.objects.filter(round=self.round).count(), len(self.teams))
        self.assertEqual(ByeTeamOverride.objects.get(round=self.round).team_id, self.teams[0].id)

    def assert_actions_forbidden(self):
        allocation = TeamSideAllocation.objects.create(round=self.round, team=self.teams[0], side=self.tournament.sides[0])
        self.assertEqual(self.client.get(self.url).status_code, 403)
        for data in self.payloads:
            with self.subTest(action=data['action']):
                self.assertEqual(self.client.post(self.url, data).status_code, 403)
        self.assertEqual(list(TeamSideAllocation.objects.filter(round=self.round).values_list('id', flat=True)), [allocation.id])
        self.assertFalse(ByeTeamOverride.objects.filter(round=self.round).exists())

    def test_direct_tournament_permission_allows_all_side_actions(self):
        UserPermission.objects.create(user=self.user, tournament=self.tournament, permission=Permission.EDIT_ALLOCATESIDES)
        self.assert_actions_allowed()

    def test_tournament_role_permission_allows_all_side_actions(self):
        role = Group.objects.create(name='Side editors', tournament=self.tournament, permissions=[Permission.EDIT_ALLOCATESIDES])
        Membership.objects.create(user=self.user, group=role)
        self.assert_actions_allowed()

    def test_unrelated_admin_permission_does_not_allow_side_actions(self):
        UserPermission.objects.create(user=self.user, tournament=self.tournament, permission=Permission.VIEW_ADMIN_DRAW)
        self.assert_actions_forbidden()

    def test_direct_permission_for_another_tournament_does_not_allow_side_actions(self):
        other = Tournament.objects.create(name='Other tournament', slug='other-tournament')
        UserPermission.objects.create(user=self.user, tournament=other, permission=Permission.EDIT_ALLOCATESIDES)
        UserPermission.objects.create(user=self.user, tournament=self.tournament, permission=Permission.VIEW_ADMIN_DRAW)
        self.assert_actions_forbidden()

    def test_role_for_another_tournament_does_not_allow_side_actions(self):
        other = Tournament.objects.create(name='Other tournament', slug='other-tournament')
        role = Group.objects.create(name='Side editors', tournament=other, permissions=[Permission.EDIT_ALLOCATESIDES])
        Membership.objects.create(user=self.user, group=role)
        UserPermission.objects.create(user=self.user, tournament=self.tournament, permission=Permission.VIEW_ADMIN_DRAW)
        self.assert_actions_forbidden()
