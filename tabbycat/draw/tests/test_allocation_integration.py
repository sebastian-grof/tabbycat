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
