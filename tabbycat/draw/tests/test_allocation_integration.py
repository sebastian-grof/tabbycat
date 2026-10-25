import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from actionlog.models import ActionLogEntry
from availability.utils import set_availability
from draw.models import Debate, DebateTeam, TeamSideAllocation
from draw.side_allocations import SideAllocationError
from participants.models import Team
from tournaments.models import Round, Tournament
from users.models import UserPermission
from users.permissions import Permission
from utils.misc import reverse_tournament


class SideAllocationIntegrationTests(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug='allocation-integration')
        self.source = Round.objects.create(
            tournament=self.tournament, seq=1, draw_type=Round.DrawType.RANDOM,
            draw_status=Round.Status.CONFIRMED,
        )
        self.target = Round.objects.create(tournament=self.tournament, seq=2, draw_type=Round.DrawType.RANDOM)
        self.tournament.current_round = self.source
        self.tournament.save()
        self.teams = [Team.objects.create(tournament=self.tournament, reference=f'Team {i}') for i in range(4)]
        set_availability(self.tournament.team_set.all(), self.target)
        self.client.force_login(get_user_model().objects.create(username='allocation-admin', is_superuser=True))

    def bulk(self, direction='opposite'):
        return self.client.post(reverse_tournament('draw-side-allocations-bulk', self.tournament), {
            'source_round_id': self.source.pk, 'target_round_id': self.target.pk, 'direction': direction,
        })

    def update(self, **data):
        return self.client.post(reverse_tournament('draw-side-allocations-update', self.tournament),
            data=json.dumps({'round_id': self.target.pk, 'team_id': self.teams[0].pk, 'side': 0, **data}),
            content_type='application/json')

    def test_jdl_opposite_uses_two_speaking_sides_and_allocates_missing_teams(self):
        self.tournament.preferences['debate_rules__teams_in_debate'] = 1
        self.tournament.preferences['debate_rules__solo_speech_format'] = True
        for team, side in zip(self.teams[:2], (0, 1)):
            DebateTeam.objects.create(debate=Debate.objects.create(round=self.source), team=team, side=side)
        self.assertEqual(self.bulk().status_code, 302)
        allocations = dict(self.target.teamsideallocation_set.values_list('team_id', 'side'))
        self.assertEqual(allocations[self.teams[0].pk], 1)
        self.assertEqual(allocations[self.teams[1].pk], 0)
        self.assertEqual(len(allocations), 4)
        self.assertCountEqual(allocations.values(), [0, 0, 1, 1])

    def test_bp_opposite_preserves_all_four_positions(self):
        self.tournament.preferences['debate_rules__teams_in_debate'] = 4
        debate = Debate.objects.create(round=self.source)
        for side, team in enumerate(self.teams):
            DebateTeam.objects.create(debate=debate, team=team, side=side)
        self.assertEqual(self.bulk().status_code, 302)
        for side, team in enumerate(self.teams):
            self.assertEqual(TeamSideAllocation.objects.get(round=self.target, team=team).side, 3 - side)

    def test_inline_update_rejects_other_tournaments_and_eliminations(self):
        foreign = Tournament.objects.create(slug='foreign-allocation')
        team = Team.objects.create(tournament=foreign, reference='Foreign')
        round_ = Round.objects.create(tournament=foreign, seq=1)
        self.assertEqual(self.update(team_id=team.pk).status_code, 400)
        self.assertEqual(self.update(round_id=round_.pk).status_code, 400)
        self.target.stage = Round.Stage.ELIMINATION
        self.target.save()
        self.assertEqual(self.update().status_code, 400)
        self.assertFalse(TeamSideAllocation.objects.exists())

    def test_failed_generation_rolls_back_partial_writes_and_does_not_log_success(self):
        def fail_after_write(target, source):
            TeamSideAllocation.objects.create(round=target, team=self.teams[0], side=1)
            raise SideAllocationError('invalid source')

        with patch('draw.views.generate_opposite_allocations', side_effect=fail_after_write):
            self.assertEqual(self.bulk().status_code, 302)
        self.assertFalse(TeamSideAllocation.objects.exists())
        self.assertFalse(ActionLogEntry.objects.filter(type=ActionLogEntry.ActionType.SIDE_PREALLOCATIONS_SAVE).exists())

    def test_unprivileged_user_cannot_mutate_allocations(self):
        self.client.force_login(get_user_model().objects.create(username='allocation-reader'))
        self.assertEqual(self.update().status_code, 403)
        self.assertEqual(self.bulk().status_code, 403)
        self.assertFalse(TeamSideAllocation.objects.exists())

    def test_matrix_is_inside_workspace_and_uses_the_same_allocations(self):
        matrix = reverse_tournament('draw-side-allocations-matrix', self.tournament)
        workspace = reverse_tournament('draw-side-allocations', self.tournament)
        response = self.client.get(workspace)
        self.assertContains(response, 'data-side-preallocation', count=len(self.teams))
        self.assertNotContains(response, f'href="{matrix}')
        self.assertRedirects(self.client.get(matrix), workspace)
        self.assertEqual(self.update(side=1).status_code, 200)
        response = self.client.get(workspace)
        field = response.context['manual_form'][f'team_{self.teams[0].pk}']
        self.assertEqual(int(field.value()), 1)

    def test_tournament_scoped_editor_can_use_matrix_and_mutations(self):
        user = get_user_model().objects.create(username='allocation-scoped-editor')
        UserPermission.objects.create(user=user, tournament=self.tournament, permission=Permission.EDIT_ALLOCATESIDES)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse_tournament('draw-side-allocations', self.tournament)).status_code, 200)
        self.assertEqual(self.update().status_code, 200)
        self.assertEqual(self.bulk(direction='same').status_code, 302)

    def test_generated_round_is_read_only_in_both_mutation_endpoints(self):
        self.target.draw_status = Round.Status.DRAFT
        self.target.save()
        self.assertEqual(self.update().status_code, 400)
        self.assertEqual(self.bulk().status_code, 302)
        self.assertFalse(TeamSideAllocation.objects.exists())
        response = self.client.get(reverse_tournament('draw-side-allocations', self.tournament), {'round_seq': self.target.seq})
        self.assertTrue(all(field.disabled for field in response.context['manual_form'].fields.values()))
        self.assertFalse(response.context['generate_form'].fields['target_round'].queryset.filter(pk=self.target.pk).exists())

    def test_drawn_round_shows_actual_sides_instead_of_old_preallocations(self):
        team = self.teams[0]
        TeamSideAllocation.objects.create(round=self.source, team=team, side=0)
        DebateTeam.objects.create(debate=Debate.objects.create(round=self.source), team=team, side=1)
        response = self.client.get(reverse_tournament('draw-side-allocations', self.tournament))
        row = next(row for row in response.context['allocation_rows'] if row['team'] == team)
        cell = next(cell for cell in row['cells'] if cell['round'] == self.source)
        self.assertEqual(cell['side'], 1)
        self.assertFalse(cell['editable'])
