from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings, TestCase

from participants.models import Adjudicator, Institution, Speaker, Team
from tournaments.models import Tournament
from utils.tests import CompletedTournamentTestMixin, ConditionalTableViewTestsMixin, TableViewTestsMixin


class PublicParticipantsViewTestCase(ConditionalTableViewTestsMixin, TestCase):

    view_toggle_preference = 'public_features__public_participants'
    view_name = 'participants-public-list'

    def expected_row_counts(self):
        return [
            self.tournament.adjudicator_set.count(),
            Speaker.objects.filter(team__tournament=self.tournament).count(),
        ]


@override_settings(STORAGES={**settings.STORAGES, 'staticfiles': {
    'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
}})
class InstitutionAdjRuleViewTests(CompletedTournamentTestMixin, TableViewTestsMixin, TestCase):
    """Regression tests for the adjudicator requirement page, which raised a
    KeyError for institutions without teams or without (non-independent)
    adjudicators."""

    view_name = 'participants-adj-rule'

    def setUp(self):
        super().setUp()
        # In the demo data, Toronto has adjudicators but no teams, and Cornell
        # has one team and only an independent adjudicator.
        self.toronto = Institution.objects.get(code='Toronto')
        self.cornell = Institution.objects.get(code='Cornell')

    def get_registered_cells(self):
        cache.clear()  # sessions are cached too, so log in afterwards
        self.client.force_login(get_user_model().objects.get(username='admin'))
        response = self.client.get(self.reverse_url(self.view_name))
        self.assertResponseOK(response)
        table = self.get_table_data(response)[0]
        self.assertEqual(table['head'][1]['key'], 'reg')
        return {row[0]['text']: row[1]['text'] for row in table['data']}

    def test_institutions_without_teams_or_adjudicators(self):
        registered = self.get_registered_cells()
        self.assertEqual(registered['Toronto'], "0/2")
        self.assertEqual(registered['Cornell'], "1/0")

    def test_registrations_in_other_tournaments_are_not_counted(self):
        other = Tournament.objects.create(slug='other', name="Other tournament")
        Team.objects.create(tournament=other, institution=self.toronto, reference="Other")
        Adjudicator.objects.create(tournament=other, institution=self.cornell, name="Other judge")
        Adjudicator.objects.create(tournament=None, institution=self.cornell, name="Global judge")

        registered = self.get_registered_cells()
        self.assertEqual(registered['Toronto'], "0/2")
        self.assertEqual(registered['Cornell'], "1/0")
