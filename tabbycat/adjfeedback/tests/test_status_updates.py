import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from actionlog.models import ActionLogEntry
from participants.models import Adjudicator
from tournaments.models import Round, Tournament
from utils.misc import reverse_tournament


class AdjudicatorStatusUpdateTests(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug='toggle-tests')
        self.tournament.current_round = Round.objects.create(tournament=self.tournament, seq=1)
        self.tournament.save()
        self.adjudicator = Adjudicator.objects.create(tournament=self.tournament, name='Judge')
        self.admin = get_user_model().objects.create(username='toggle-admin', is_superuser=True)
        self.client.force_login(self.admin)

    def post_status(self, status, value=True, adjudicator=None):
        return self.client.post(
            reverse_tournament(f'adjfeedback-set-adj-{status}-status', self.tournament),
            data=json.dumps({'id': (adjudicator or self.adjudicator).pk, status: value}),
            content_type='application/json',
        )

    def test_both_statuses_persist_and_are_logged(self):
        for status, field, action in (
            ('breaking', 'breaking', ActionLogEntry.ActionType.ADJUDICATOR_BREAK_SET),
            ('tester', 'is_tester', ActionLogEntry.ActionType.ADJUDICATOR_TESTER_SET),
        ):
            for value in (True, False):
                with self.subTest(status=status, value=value):
                    self.assertEqual(self.post_status(status, value).status_code, 200)
                    self.adjudicator.refresh_from_db()
                    self.assertEqual(getattr(self.adjudicator, field), value)
            self.assertEqual(ActionLogEntry.objects.filter(type=action, tournament=self.tournament).count(), 2)

    def test_unprivileged_user_cannot_change_either_status(self):
        self.client.force_login(get_user_model().objects.create(username='no-permissions'))
        for status in ('breaking', 'tester'):
            self.assertEqual(self.post_status(status).status_code, 403)
        self.assertFalse(ActionLogEntry.objects.exists())

    def test_other_tournament_and_invalid_status_are_rejected(self):
        other = Tournament.objects.create(slug='other-toggle-tests')
        foreign = Adjudicator.objects.create(tournament=other, name='Other judge')
        for status in ('breaking', 'tester'):
            self.assertEqual(self.post_status(status, adjudicator=foreign).status_code, 400)
            self.assertEqual(self.post_status(status, value='false').status_code, 400)
        self.assertFalse(ActionLogEntry.objects.exists())
