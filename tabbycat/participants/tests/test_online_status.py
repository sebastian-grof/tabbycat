import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils.translation import gettext, override
from rest_framework.test import APIClient

from adjallocation.serializers import EditPanelOrDebateAdjSerializer
from availability.models import RoundAvailability
from participants.admin import AdjudicatorForm as DatabaseAdjudicatorForm
from participants.display import name_with_online_status, name_with_online_status_text
from participants.models import Adjudicator, Person
from registration.forms import AdjudicatorForm, AdminAdjudicatorEditForm
from utils.misc import reverse_round, reverse_tournament
from utils.tables import TabbycatTableBuilder
from utils.tests import CompletedTournamentTestMixin


@override_settings(STORAGES={**settings.STORAGES, 'staticfiles': {
    'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
}})
class OnlineAdjudicatorTests(CompletedTournamentTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.enterContext(override('en'))
        self.adj = self.tournament.adjudicator_set.first()
        self.staff = get_user_model().objects.get(username='admin')
        self.tournament.preferences['public_features__public_participants'] = True
        self.tournament.preferences['public_features__public_record'] = True
        self.tournament.preferences['ui_options__participant_code_names'] = 'off'

    def mark_online(self):
        self.adj.is_online = True
        self.adj.save()

    def test_existing_and_new_judges_default_offline(self):
        self.assertFalse(self.tournament.adjudicator_set.filter(is_online=True).exists())
        new = Adjudicator.objects.create(name='New judge', tournament=self.tournament)
        new.refresh_from_db()
        self.assertFalse(new.is_online)

    def test_registration_editor_saves_and_clears_status(self):
        url = reverse_tournament('reg-adjudicator-edit', self.tournament, kwargs={'pk': self.adj.pk})
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(url), 'Mark as online')
        availability_count = RoundAvailability.objects.count()
        data = {'name': self.adj.name, 'base_score': self.adj.base_score, 'registration_status': self.adj.registration_status}
        for online in (True, False):
            response = self.client.post(url, {**data, 'is_online': 'on'} if online else data)
            self.assertEqual(response.status_code, 302)
            self.adj.refresh_from_db()
            self.assertEqual(self.adj.is_online, online)
            form = AdminAdjudicatorEditForm(self.tournament, instance=self.adj)
            self.assertEqual(form['is_online'].value(), online)
        self.assertEqual(RoundAvailability.objects.count(), availability_count)

    def test_database_editor_saves_and_clears_status(self):
        data = {'name': self.adj.name, 'base_score': self.adj.base_score,
                'tournament': self.tournament.pk, 'registration_status': self.adj.registration_status}
        for online in (True, False):
            form = DatabaseAdjudicatorForm(instance=self.adj, data={**data, 'is_online': online})
            for field in ('institution_conflicts', 'team_conflicts', 'adjudicator_conflicts'):
                form.fields[field].required = False
            self.assertTrue(form.is_valid(), form.errors)
            form.save()
            self.adj.refresh_from_db()
            self.assertEqual(self.adj.is_online, online)
        self.client.force_login(self.staff)
        url = reverse('admin:participants_adjudicator_change', args=[self.adj.pk])
        self.assertContains(self.client.get(url), 'Mark as online')

    def test_public_registration_cannot_set_status(self):
        form = AdjudicatorForm(self.tournament, data={'name': 'Public judge', 'is_online': 'on'})
        self.assertNotIn('is_online', form.fields)
        self.assertFalse(form.instance.is_online)

    def test_public_api_exposes_status_and_denies_writes(self):
        self.mark_online()
        url = reverse_tournament('api-adjudicator-detail', self.tournament, kwargs={'pk': self.adj.pk})
        client = APIClient()
        response = client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIs(response.data['is_online'], True)
        response = client.patch(url, {'is_online': False}, format='json')
        self.assertIn(response.status_code, (401, 403))
        user = get_user_model().objects.create_user(username='no_permissions')
        client.force_authenticate(user)
        self.assertEqual(client.patch(url, {'is_online': False}, format='json').status_code, 403)
        self.adj.refresh_from_db()
        self.assertTrue(self.adj.is_online)

    def test_authorized_api_can_set_and_clear_status(self):
        client = APIClient()
        client.force_authenticate(self.staff)
        url = reverse_tournament('api-adjudicator-detail', self.tournament, kwargs={'pk': self.adj.pk})
        for online in (True, False):
            response = client.patch(url, {'is_online': online}, format='json')
            self.assertEqual(response.status_code, 200, response.data)
            self.adj.refresh_from_db()
            self.assertEqual(self.adj.is_online, online)

    def test_allocators_receive_the_flag(self):
        self.mark_online()
        self.adj.available = True
        data = EditPanelOrDebateAdjSerializer(self.adj, context={'feedback_weight': 0}).data
        self.assertIs(data['is_online'], True)
        self.assertIs(data['available'], True)
        self.client.force_login(self.staff)
        round = self.tournament.round_set.first()
        for view in ('edit-debate-adjudicators', 'edit-panel-adjudicators'):
            response = self.client.get(reverse_round(view, round))
            self.assertEqual(response.status_code, 200)
            items = json.loads(response.context['vueAllocatableItems'])
            self.assertTrue(next(adj for adj in items if adj['id'] == self.adj.pk)['is_online'])

    def test_shared_judge_list_escapes_names_and_preserves_sorting(self):
        self.mark_online()
        self.adj.name = '<img src=x onerror=alert(1)>'
        table = TabbycatTableBuilder(tournament=self.tournament)
        table.add_adjudicator_columns([self.adj], show_metadata=False)
        cell = table.data[0][0]
        self.assertIn('online-status', cell['text'])
        self.assertIn('&lt;img', cell['text'])
        self.assertNotIn('<img', cell['text'])
        self.assertNotIn('online-status', cell['sort'])
        self.assertEqual(self.adj.name, '<img src=x onerror=alert(1)>')

    def test_anonymous_judges_remain_redacted(self):
        self.mark_online()
        self.adj.anonymous = True
        table = TabbycatTableBuilder(tournament=self.tournament)
        table.add_adjudicator_columns([self.adj])
        cell = table.data[0][0]
        self.assertIn(f'<em>{gettext("Redacted")}</em>', cell['text'])
        self.assertNotIn(self.adj.name, cell['text'])
        self.assertIn('online-status', cell['text'])

    def test_draws_show_status_beside_judge_roles(self):
        debate = self.tournament.round_set.first().debate_set.first()
        adj = debate.adjudicators.chair
        adj.is_online = True
        adj.save()
        table = TabbycatTableBuilder(tournament=self.tournament)
        table.add_debate_adjudicators_column([debate])
        self.assertIn('online-status', table.data[0][0]['text'])
        for template in ('tables/debate_adjudicators.html', 'tables/debate_adjudicators_compact.html'):
            html = render_to_string(template, {'debate': debate, 'tournament': self.tournament})
            self.assertIn('online-status', html)

    def test_template_status_and_plain_text_fallback(self):
        self.mark_online()
        self.assertIn('online-status', name_with_online_status(self.adj, self.adj.name))
        self.assertEqual(name_with_online_status_text(self.adj, 'Judge'), 'Judge (Online)')
        self.assertIn('online-status', render_to_string('includes/public_enter_results_info.html', {
            'private_url': True, 'adjudicator': self.adj, 'tournament': self.tournament,
        }))
        # Private URL pages and feedback authors sometimes have a base Person.
        person = Person.objects.get(pk=self.adj.pk)
        html = Template('{% load debate_tags %}{% online_status person %}').render(Context({'person': person}))
        self.assertIn('online-status', html)

    def test_offline_judges_have_no_badge(self):
        self.assertNotIn('online-status', name_with_online_status(self.adj, self.adj.name))
        self.assertEqual(name_with_online_status_text(self.adj, 'Judge'), 'Judge')

    def test_checkin_data_contains_status(self):
        self.mark_online()
        self.client.force_login(self.staff)
        response = self.client.get(reverse_tournament('admin-people-statuses', self.tournament))
        self.assertEqual(response.status_code, 200)
        adjs = json.loads(response.context['adjudicators'])
        self.assertTrue(next(adj for adj in adjs if adj['id'] == self.adj.pk)['is_online'])

    def test_public_records_show_status(self):
        self.mark_online()
        url = reverse_tournament('participants-public-adjudicator-record', self.tournament, kwargs={'pk': self.adj.pk})
        self.assertContains(self.client.get(url), 'online-status')
