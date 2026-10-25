from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from options.forms import tournament_preference_form_builder
from tournaments.models import Tournament


class TournamentPreferenceFormTests(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create()

    def tearDown(self):
        self.tournament.delete()

    def test_falsy_preference_change(self):
        # Test that get_pref() doesn't get the current value if falsy in the posted data
        form = tournament_preference_form_builder(self.tournament, section='data_entry')()
        self.tournament.preferences['data_entry__public_use_password'] = False
        form.cleaned_data = {'data_entry__public_use_password': True, 'data_entry__public_password': ''}
        with self.assertRaises(ValidationError) as cm:
            form.clean()
        self.assertIsNotNone(cm.exception.args[0].get('data_entry__public_password'))

    def test_validation_between_prefs(self):
        tests = [
            ('scoring', (('score_min', Decimal('100')), ('score_max', Decimal('0')))),
            ('scoring', (('reply_score_min', Decimal('100')), ('reply_score_max', Decimal('0')))),
            ('feedback', (('adj_min_score', 100), ('adj_max_score', 0))),
            ('draw_rules', (('draw_side_allocations', 'balance'), ('draw_odd_bracket', 'intermediate1'))),
            ('debate_rules', (('ballots_per_debate_prelim', 'per-adj'), ('teams_in_debate', 4))),
            ('debate_rules', (('solo_speech_format', True), ('teams_in_debate', 2))),
            ('debate_rules', (('teams_in_debate', 1), ('solo_speech_format', False))),
            ('data_entry', (('public_use_password', True), ('public_password', ''))),
            ('ui_options', (('team_code_names', 'everywhere'), ('show_team_institutions', True))),
        ]
        for section, prefs in tests:
            with self.subTest(section=section, prefs=[p[0] for p in prefs]):
                form = tournament_preference_form_builder(self.tournament, section=section)()
                form.cleaned_data = {section + "__" + pref: val for pref, val in prefs}
                with self.assertRaises(ValidationError) as cm:
                    form.clean()
                self.assertIsNotNone(cm.exception.args[0].get(section + "__" + prefs[-1][0]))

    def test_sda_weighting_rejects_median(self):
        self.tournament.preferences['debate_rules__adjudicator_weighting'] = 'weighted-to-three'
        for section, name, value in (
            ('scoring', 'score_aggregation_function', 'median'),
        ):
            with self.subTest(preference=name):
                form = tournament_preference_form_builder(self.tournament, section=section)()
                form.cleaned_data = {section + '__' + name: value}
                with self.assertRaises(ValidationError):
                    form.clean()

    def test_sda_weighting_allows_self_split(self):
        self.tournament.preferences['debate_rules__adjudicator_weighting'] = 'weighted-to-three'
        form = tournament_preference_form_builder(self.tournament, section='data_entry')()
        form.cleaned_data = {'data_entry__allow_self_split_ballots': True}
        form.clean()

    def test_weighting_cannot_switch_to_sda_with_median_enabled(self):
        self.tournament.preferences['scoring__score_aggregation_function'] = 'median'
        form = tournament_preference_form_builder(self.tournament, section='debate_rules')()
        form.cleaned_data = {'debate_rules__adjudicator_weighting': 'weighted-to-three'}
        with self.assertRaises(ValidationError):
            form.clean()
