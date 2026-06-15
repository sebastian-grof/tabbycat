from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _

from participants.models import Team
from tournaments.models import Tournament

from ..models import (
    BreakLeague,
    BreakRegion,
    BreakSeason,
    BreakSpeaker,
    BreakSpeakerTournamentParticipation,
    BreakTeam,
    BreakTeamLink,
    BreakTeamTournamentResult,
    BreakTournament,
    BreaksPermission,
    GlobalBreaksPermission,
)
from ..services import (
    calculate_rankings,
    calculate_region_quotas,
    publish_public_breaks_snapshot,
    prune_unused_break_identities,
    reassign_break_team_link,
)


class BreaksPermissionTests(TestCase):
    def test_public_breaks_index_is_anonymous(self):
        response = self.client.get(reverse('public-breaks-index'))
        self.assertEqual(response.status_code, 200)

    def test_breaks_index_requires_global_permission(self):
        user = get_user_model().objects.create_user(username='tab', password='pw')
        self.client.login(username='tab', password='pw')
        response = self.client.get(reverse('seasonbreaks-index'))
        self.assertEqual(response.status_code, 403)

        GlobalBreaksPermission.objects.create(user=user, permission=BreaksPermission.VIEW)
        response = self.client.get(reverse('seasonbreaks-index'))
        self.assertEqual(response.status_code, 200)


class BreakLeagueManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tab', password='pw')
        GlobalBreaksPermission.objects.create(user=self.user, permission=BreaksPermission.VIEW)
        GlobalBreaksPermission.objects.create(user=self.user, permission=BreaksPermission.EDIT)
        self.client.force_login(self.user)

    def test_can_create_league_from_break_management(self):
        response = self.client.post(reverse('seasonbreaks-index'), {
            'action': 'create_league',
            'name': 'KSD',
            'slug': '',
        })

        self.assertRedirects(response, reverse('seasonbreaks-index'))
        self.assertTrue(BreakLeague.objects.filter(name='KSD', slug='ksd').exists())

    def test_can_create_season_with_custom_league(self):
        league = BreakLeague.objects.create(name='KSD', slug='ksd')

        response = self.client.post(reverse('seasonbreaks-index'), {
            'action': 'create_season',
            'name': 'KSD 2026/2027',
            'slug': 'ksd-2026-2027',
            'league': league.id,
            'regional_slots': 4,
            'invited_teams': 0,
            'active': 'on',
        })

        season = BreakSeason.objects.get(slug='ksd-2026-2027')
        self.assertRedirects(response, reverse('seasonbreaks-season-overview', kwargs={'season_slug': season.slug}))
        self.assertEqual(season.league, league)

    def test_cannot_delete_league_with_seasons(self):
        league = BreakLeague.objects.create(name='KSD', slug='ksd')
        BreakSeason.objects.create(name='KSD 2026/2027', slug='ksd-2026-2027', league=league)

        response = self.client.post(reverse('seasonbreaks-index'), {
            'action': 'delete_league',
            'league_id': league.id,
        })

        self.assertRedirects(response, reverse('seasonbreaks-index'))
        self.assertTrue(BreakLeague.objects.filter(id=league.id).exists())

    def test_can_delete_season_from_overview(self):
        league = BreakLeague.objects.create(name='KSD', slug='ksd')
        season = BreakSeason.objects.create(name='KSD 2026/2027', slug='ksd-2026-2027', league=league)
        region = BreakRegion.objects.create(season=season, name='West')
        tournament = Tournament.objects.create(name='West 1', short_name='W1', slug='w1')
        BreakTournament.objects.create(season=season, tournament=tournament, region=region)

        response = self.client.post(reverse('seasonbreaks-season-overview', kwargs={'season_slug': season.slug}), {
            'action': 'delete_season',
        })

        self.assertRedirects(response, reverse('seasonbreaks-index'))
        self.assertFalse(BreakSeason.objects.filter(id=season.id).exists())
        self.assertFalse(BreakRegion.objects.filter(id=region.id).exists())
        self.assertFalse(BreakTournament.objects.filter(tournament=tournament).exists())

    def test_can_create_and_update_regions_from_region_tab(self):
        league = BreakLeague.objects.create(name='KSD', slug='ksd')
        season = BreakSeason.objects.create(name='KSD 2026/2027', slug='ksd-2026-2027', league=league)

        response = self.client.post(reverse('seasonbreaks-regions', kwargs={'season_slug': season.slug}), {
            'action': 'add_region',
            'name': 'West',
            'source_region': '',
            'seq': 1,
            'public_visible': 'on',
        })

        region = BreakRegion.objects.get(season=season, name='West')
        self.assertRedirects(response, reverse('seasonbreaks-regions', kwargs={'season_slug': season.slug}))
        self.assertTrue(region.public_visible)

        response = self.client.post(reverse('seasonbreaks-regions', kwargs={'season_slug': season.slug}), {
            'action': 'update_region',
            'region': region.id,
            f'region-{region.id}-name': 'West hidden',
            f'region-{region.id}-source_region': '',
            f'region-{region.id}-seq': 4,
        })

        region.refresh_from_db()
        self.assertRedirects(response, reverse('seasonbreaks-regions', kwargs={'season_slug': season.slug}))
        self.assertEqual(region.name, 'West hidden')
        self.assertEqual(region.seq, 4)
        self.assertFalse(region.public_visible)

        response = self.client.get(reverse('seasonbreaks-regions', kwargs={'season_slug': season.slug}))
        self.assertContains(response, 'West hidden')
        self.assertContains(response, _("Hidden from public page"))


class BreaksCalculationTests(TestCase):
    def setUp(self):
        self.league = BreakLeague.objects.get(slug='sdl')
        self.season = BreakSeason.objects.create(
            name='SDL 2025/26', slug='sdl-2025', league=self.league,
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

    def test_expected_tournaments_drives_best_n_minus_one_window(self):
        # West only has two tournaments frozen so far, but the region is expected
        # to run three this season. With N=3 the rule counts the best two results,
        # so a team that played both gets them summed instead of just its best one.
        team = self._team_with_members('Onda', self.west, [self.bt_w1, self.bt_w2], [
            (self.bt_w1, 3, 9, 593),
            (self.bt_w2, 3, 9, 561),
        ])

        # Default (expected=0) falls back to the two counting tournaments -> best 1.
        rankings = calculate_rankings(self.season)[self.west.id]
        self.assertEqual(rankings[0]['team'], team)
        self.assertEqual(rankings[0]['wins'], 3)
        self.assertEqual(rankings[0]['required_tournaments'], 1)

        self.west.expected_tournaments = 3
        self.west.save(update_fields=['expected_tournaments'])

        rankings = calculate_rankings(self.season)[self.west.id]
        self.assertEqual(rankings[0]['wins'], 6)
        self.assertEqual(rankings[0]['ballots'], 18)
        self.assertEqual(rankings[0]['speaker_score'], 1154)
        self.assertEqual(rankings[0]['participations'], 2)
        self.assertEqual(rankings[0]['required_tournaments'], 2)
        self.assertTrue(rankings[0]['eligible'])

    def test_rankings_sort_by_performance_not_eligibility(self):
        # A stronger but ineligible team must rank above a weaker eligible one;
        # eligibility only governs advancement, not standings position.
        eligible = self._team_with_members('Eligible', self.west, [self.bt_w1, self.bt_w2], [
            (self.bt_w1, 2, 6, 600),
            (self.bt_w2, 2, 6, 600),
        ])
        strong_solo = BreakTeam.objects.create(season=self.season, name='Strong solo', region=self.west)
        BreakTeamTournamentResult.objects.create(
            break_tournament=self.bt_w1, break_team=strong_solo, wins=3, ballots=9,
            speaker_score=700, rounds_debated=3, majority_debated=True,
        )

        rankings = calculate_rankings(self.season)[self.west.id]
        self.assertEqual(rankings[0]['team'], strong_solo)
        self.assertEqual(rankings[0]['wins'], 3)
        self.assertFalse(rankings[0]['eligible'])
        self.assertFalse(rankings[0]['advancing'])
        self.assertEqual(rankings[1]['team'], eligible)
        self.assertTrue(rankings[1]['eligible'])
        self.assertTrue(rankings[1]['advancing'])

    def test_reassign_team_link_merges_results_and_removes_duplicate(self):
        # Same team entered under two spellings ("OnDa" / "ONDA") across two
        # tournaments became two identities. Merging the link must carry the
        # frozen results and participations over and drop the empty duplicate.
        real_onda = Team.objects.create(
            tournament=self.tournament_w1, reference='OnDa', use_institution_prefix=False)
        real_onda_caps = Team.objects.create(
            tournament=self.tournament_w2, reference='ONDA', use_institution_prefix=False)

        identity_a = BreakTeam.objects.create(season=self.season, name='OnDa', region=self.west)
        identity_b = BreakTeam.objects.create(season=self.season, name='ONDA', region=self.west)
        link_a = BreakTeamLink.objects.create(season=self.season, break_team=identity_a, team=real_onda)
        BreakTeamLink.objects.create(season=self.season, break_team=identity_b, team=real_onda_caps)

        BreakTeamTournamentResult.objects.create(
            break_tournament=self.bt_w1, break_team=identity_a, wins=3, ballots=9,
            speaker_score=700, rounds_debated=3, majority_debated=True)
        BreakTeamTournamentResult.objects.create(
            break_tournament=self.bt_w2, break_team=identity_b, wins=2, ballots=6,
            speaker_score=600, rounds_debated=3, majority_debated=True)
        for index in range(2):
            speaker = BreakSpeaker.objects.create(season=self.season, name=f'Shared speaker {index}')
            BreakSpeakerTournamentParticipation.objects.create(
                break_tournament=self.bt_w1, break_speaker=speaker, break_team=identity_a, speeches=2, rounds=2)
            BreakSpeakerTournamentParticipation.objects.create(
                break_tournament=self.bt_w2, break_speaker=speaker, break_team=identity_b, speeches=2, rounds=2)

        reassign_break_team_link(link_a, identity_b)

        self.assertFalse(BreakTeam.objects.filter(id=identity_a.id).exists())
        self.assertEqual(
            BreakTeamTournamentResult.objects.get(break_tournament=self.bt_w1).break_team, identity_b)
        self.assertFalse(
            BreakSpeakerTournamentParticipation.objects.filter(break_team=identity_a).exists())

        rankings = calculate_rankings(self.season)[self.west.id]
        self.assertEqual(len(rankings), 1)
        row = rankings[0]
        self.assertEqual(row['team'], identity_b)
        self.assertEqual(row['participations'], 2)
        self.assertEqual(row['wins'], 3)  # best 1 of 2 results
        self.assertTrue(row['eligible'])
        self.assertEqual(row['eligible_members'], 2)

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

    def test_prune_unused_break_identities_removes_only_unused_candidates(self):
        unused_team = BreakTeam.objects.create(season=self.season, name='Unused Team', region=self.west)
        used_team = BreakTeam.objects.create(season=self.season, name='Used Team', region=self.west)
        unused_speaker = BreakSpeaker.objects.create(season=self.season, name='Unused Speaker')
        used_speaker = BreakSpeaker.objects.create(season=self.season, name='Used Speaker')

        BreakTeamTournamentResult.objects.create(
            break_tournament=self.bt_w1, break_team=used_team, wins=1, ballots=3,
            speaker_score=500, rounds_debated=3, majority_debated=True,
        )
        BreakSpeakerTournamentParticipation.objects.create(
            break_tournament=self.bt_w1, break_speaker=used_speaker, break_team=used_team,
            speeches=2, rounds=2,
        )

        deleted = prune_unused_break_identities(
            self.season,
            team_ids=[unused_team.id, used_team.id],
            speaker_ids=[unused_speaker.id, used_speaker.id],
        )

        self.assertEqual(deleted['teams'], 1)
        self.assertEqual(deleted['speakers'], 1)
        self.assertFalse(BreakTeam.objects.filter(id=unused_team.id).exists())
        self.assertTrue(BreakTeam.objects.filter(id=used_team.id).exists())
        self.assertFalse(BreakSpeaker.objects.filter(id=unused_speaker.id).exists())
        self.assertTrue(BreakSpeaker.objects.filter(id=used_speaker.id).exists())

    def test_public_breaks_only_show_public_published_seasons(self):
        response = self.client.get(reverse('public-breaks-index'))
        self.assertNotContains(response, self.season.name)

        self.season.public = True
        self.season.save(update_fields=['public'])
        response = self.client.get(reverse('public-breaks-index'))
        self.assertNotContains(response, self.season.name)

        publish_public_breaks_snapshot(self.season)
        response = self.client.get(reverse('public-breaks-index'))
        self.assertContains(response, self.season.name)

    def test_public_snapshot_freezes_region_and_global_rankings_until_republished(self):
        team = self._team_with_members('West A', self.west, [self.bt_w1], [(self.bt_w1, 1, 3, 500)])
        self._team_with_members('East A', self.east, [self.bt_e1], [(self.bt_e1, 2, 6, 600)])
        self.season.public = True
        self.season.public_global_ranking = True
        self.season.save(update_fields=['public', 'public_global_ranking'])
        publish_public_breaks_snapshot(self.season)

        response = self.client.get(reverse('public-breaks-season', kwargs={'season_slug': self.season.slug}))
        self.assertContains(response, 'West A')
        self.assertContains(response, 'East A')
        self.assertNotContains(response, 'Status')
        self.assertEqual(response.context['global_rows'][1]['wins'], 1.0)
        self.assertEqual(response.context['regions'][0]['slots'], 2)

        BreakTeamTournamentResult.objects.filter(break_team=team).update(wins=99, ballots=99, speaker_score=9999)
        response = self.client.get(reverse('public-breaks-season', kwargs={'season_slug': self.season.slug}))
        self.assertEqual(response.context['global_rows'][1]['wins'], 1.0)

        publish_public_breaks_snapshot(self.season)
        response = self.client.get(reverse('public-breaks-season', kwargs={'season_slug': self.season.slug}))
        self.assertEqual(response.context['global_rows'][0]['wins'], 99.0)

    def test_public_region_visibility_uses_published_snapshot(self):
        self._team_with_members('West A', self.west, [self.bt_w1], [(self.bt_w1, 1, 3, 500)])
        self._team_with_members('East A', self.east, [self.bt_e1], [(self.bt_e1, 2, 6, 600)])
        self.season.public = True
        self.season.public_global_ranking = True
        self.season.save(update_fields=['public', 'public_global_ranking'])
        publish_public_breaks_snapshot(self.season)

        self.west.public_visible = False
        self.west.save(update_fields=['public_visible'])

        response = self.client.get(reverse('public-breaks-season', kwargs={'season_slug': self.season.slug}))
        self.assertContains(response, 'West A')
        self.assertEqual([region['name'] for region in response.context['regions']], ['West', 'East'])

        publish_public_breaks_snapshot(self.season)
        response = self.client.get(reverse('public-breaks-season', kwargs={'season_slug': self.season.slug}))
        self.assertNotContains(response, 'West A')
        self.assertContains(response, 'East A')
        self.assertEqual([region['name'] for region in response.context['regions']], ['East'])
        self.assertEqual([row['team'] for row in response.context['global_rows']], ['East A'])

        response = self.client.get(reverse('public-breaks-region', kwargs={
            'season_slug': self.season.slug,
            'region_id': self.west.id,
        }))
        self.assertEqual(response.status_code, 404)

    def test_public_global_ranking_excludes_nonleague_tournaments(self):
        self._team_with_members('West A', self.west, [self.bt_w1, self.bt_open], [
            (self.bt_w1, 1, 3, 500),
            (self.bt_open, 99, 99, 9999),
        ])
        self.season.public = True
        self.season.save(update_fields=['public'])
        publish_public_breaks_snapshot(self.season)

        response = self.client.get(reverse('public-breaks-season', kwargs={'season_slug': self.season.slug}))
        self.assertEqual(response.context['global_rows'][0]['wins'], 1.0)
        self.assertNotContains(response, 'Status')

    def test_public_region_page_uses_published_snapshot_without_status_column(self):
        self._team_with_members('West A', self.west, [self.bt_w1], [(self.bt_w1, 1, 3, 500)])
        self.season.public = True
        self.season.save(update_fields=['public'])
        publish_public_breaks_snapshot(self.season)

        response = self.client.get(reverse('public-breaks-region', kwargs={
            'season_slug': self.season.slug,
            'region_id': self.west.id,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'West A')
        self.assertContains(response, _("Speaker points"))
        self.assertNotContains(response, 'Status')

    def test_public_global_ranking_toggle_controls_card_visibility(self):
        self._team_with_members('West A', self.west, [self.bt_w1], [(self.bt_w1, 1, 3, 500)])
        self.season.public = True
        self.season.public_global_ranking = False
        self.season.save(update_fields=['public', 'public_global_ranking'])
        publish_public_breaks_snapshot(self.season)

        url = reverse('public-breaks-season', kwargs={'season_slug': self.season.slug})
        response = self.client.get(url)
        self.assertFalse(response.context['show_global_ranking'])
        self.assertNotContains(response, _("Global ranking"))
        self.assertNotContains(response, 'West A')

        self.season.public_global_ranking = True
        self.season.save(update_fields=['public_global_ranking'])
        publish_public_breaks_snapshot(self.season)
        response = self.client.get(url)
        self.assertTrue(response.context['show_global_ranking'])
        self.assertContains(response, _("Global ranking"))
        self.assertContains(response, 'West A')

    def test_legacy_snapshot_without_toggle_still_shows_global_ranking(self):
        self._team_with_members('West A', self.west, [self.bt_w1], [(self.bt_w1, 1, 3, 500)])
        self.season.public = True
        self.season.save(update_fields=['public'])
        publish_public_breaks_snapshot(self.season)

        # Simulate a snapshot published before the toggle existed.
        snapshot = dict(self.season.public_snapshot)
        snapshot.pop('show_global_ranking', None)
        self.season.public_snapshot = snapshot
        self.season.save(update_fields=['public_snapshot'])

        response = self.client.get(reverse('public-breaks-season', kwargs={'season_slug': self.season.slug}))
        self.assertTrue(response.context['show_global_ranking'])
        self.assertContains(response, 'West A')

    def test_publish_form_persists_global_ranking_toggle(self):
        user = get_user_model().objects.create_user(username='breaks-admin', password='pw')
        GlobalBreaksPermission.objects.create(user=user, permission=BreaksPermission.VIEW)
        GlobalBreaksPermission.objects.create(user=user, permission=BreaksPermission.EDIT)
        self.client.force_login(user)

        overview_url = reverse('seasonbreaks-season-overview', kwargs={'season_slug': self.season.slug})
        response = self.client.post(overview_url, {
            'action': 'publish_public_snapshot',
            'show_global_ranking': '1',
        })
        self.assertRedirects(response, overview_url)
        self.season.refresh_from_db()
        self.assertTrue(self.season.public_global_ranking)
        self.assertTrue(self.season.public_snapshot['show_global_ranking'])

        response = self.client.post(overview_url, {'action': 'publish_public_snapshot'})
        self.season.refresh_from_db()
        self.assertFalse(self.season.public_global_ranking)
        self.assertFalse(self.season.public_snapshot['show_global_ranking'])

    def test_admin_global_ranking_preview_lists_teams_without_publishing(self):
        self._team_with_members('West A', self.west, [self.bt_w1], [(self.bt_w1, 1, 3, 500)])
        self._team_with_members('East A', self.east, [self.bt_e1], [(self.bt_e1, 2, 6, 600)])
        user = get_user_model().objects.create_user(username='breaks-view', password='pw')
        GlobalBreaksPermission.objects.create(user=user, permission=BreaksPermission.VIEW)
        self.client.force_login(user)

        url = reverse('seasonbreaks-global-ranking', kwargs={'season_slug': self.season.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['team'] for row in response.context['rows']], ['East A', 'West A'])
        self.assertContains(response, 'East A')
        self.assertContains(response, 'West A')
        # Still nothing published publicly.
        self.assertIsNone(self.season.public_published_at)

    def test_admin_global_ranking_preview_excludes_nonpublic_regions(self):
        self._team_with_members('West A', self.west, [self.bt_w1], [(self.bt_w1, 1, 3, 500)])
        self._team_with_members('East A', self.east, [self.bt_e1], [(self.bt_e1, 2, 6, 600)])
        self.west.public_visible = False
        self.west.save(update_fields=['public_visible'])
        user = get_user_model().objects.create_user(username='breaks-view2', password='pw')
        GlobalBreaksPermission.objects.create(user=user, permission=BreaksPermission.VIEW)
        self.client.force_login(user)

        url = reverse('seasonbreaks-global-ranking', kwargs={'season_slug': self.season.slug})
        response = self.client.get(url)
        self.assertEqual([row['team'] for row in response.context['rows']], ['East A'])
        self.assertNotContains(response, 'West A')
