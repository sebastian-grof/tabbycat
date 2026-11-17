import logging

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from draw.models import Debate
from draw.types import DebateSide
from utils.misc import add_query_string_parameter
from utils.tests import CompletedTournamentTestMixin, suppress_logs


class FixDebateTeamsViewTests(CompletedTournamentTestMixin, TestCase):
    """Regression tests for the page listing debates without exactly one team
    per side, which raised "TypeError: keywords must be strings" because side
    codes are integers."""

    view_name = 'tournament-fix-debate-teams'

    def setUp(self):
        super().setUp()
        self.debates = Debate.objects.filter(round__tournament=self.tournament).order_by('id')

    def get_page(self, user=None):
        # Clear cached tournament and preferences. Sessions are cached too, so
        # log in afterwards.
        cache.clear()
        if user is not None:
            self.client.force_login(user)
        return self.client.get(self.reverse_url(self.view_name))

    def get_incomplete_debates(self):
        response = self.get_page(get_user_model().objects.get(username='admin'))
        self.assertEqual(response.status_code, 200)
        return {debate.id: debate.teams_on_each_side for debate in response.context['incomplete_debates']}

    def test_no_incomplete_debates(self):
        self.assertEqual(self.get_incomplete_debates(), {})

    def test_lists_debates_with_duplicate_or_missing_sides(self):
        duplicate, missing = self.debates[:2]
        aff_team = duplicate.debateteam_set.get(side=DebateSide.AFF).team
        neg_team = duplicate.debateteam_set.get(side=DebateSide.NEG).team
        duplicate.debateteam_set.filter(side=DebateSide.NEG).update(side=DebateSide.AFF)
        missing.debateteam_set.filter(side=DebateSide.AFF).delete()
        missing_neg_team = missing.debateteam_set.get(side=DebateSide.NEG).team

        incomplete = self.get_incomplete_debates()
        self.assertEqual(set(incomplete), {duplicate.id, missing.id})
        self.assertCountEqual(incomplete[duplicate.id][DebateSide.AFF], [aff_team, neg_team])
        self.assertEqual(incomplete[duplicate.id][DebateSide.NEG], [])
        self.assertEqual(incomplete[missing.id][DebateSide.AFF], [])
        self.assertEqual(incomplete[missing.id][DebateSide.NEG], [missing_neg_team])

    def test_bye_debates_are_not_listed(self):
        bye = self.debates[0]
        bye.debateteam_set.filter(side=DebateSide.NEG).delete()
        bye.debateteam_set.update(side=DebateSide.BYE)

        self.assertEqual(self.get_incomplete_debates(), {})

    def test_one_team_per_debate_format(self):
        self.tournament.preferences['debate_rules__teams_in_debate'] = 1
        solo, empty = self.debates[:2]
        solo.debateteam_set.filter(side=DebateSide.NEG).delete()
        empty.debateteam_set.all().delete()

        # Every other debate in the demo data has two teams
        incomplete = self.get_incomplete_debates()
        self.assertEqual(set(incomplete), set(self.debates.values_list('id', flat=True)) - {solo.id})
        self.assertEqual(incomplete[empty.id], {DebateSide.AFF: [], DebateSide.NEG: []})

    def test_anonymous_user_is_sent_to_login(self):
        response = self.get_page()
        url = self.reverse_url(self.view_name)
        self.assertRedirects(response, add_query_string_parameter(reverse('login'), 'next', url))

    def test_user_without_admin_access_is_denied(self):
        user = get_user_model().objects.create_user(username='plain', password='password')
        with suppress_logs('django.request', logging.WARNING):
            response = self.get_page(user)
        self.assertEqual(response.status_code, 403)
