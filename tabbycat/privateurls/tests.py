from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.test import TestCase

from adjallocation.models import DebateAdjudicator
from adjfeedback.models import AdjudicatorFeedback
from options.forms import tournament_preference_form_builder
from options.presets import JDLFirstCategoryPreferences, JDLFormatPreferences, NonLeagueTournamentsPreferences, SDLFormatPreferences
from participants.models import Adjudicator, Institution, Speaker, Team
from results.models import BallotSubmission, TeamScore
from tournaments.models import Round, Tournament
from utils.misc import reverse_tournament


class MissingTeamFeedbackTests(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug='missing-feedback', name='Missing Feedback')
        self.tournament.preferences['feedback__show_missing_team_feedback'] = True
        self.tournament.preferences['feedback__feedback_from_teams'] = 'all-voting-adjs'
        self.tournament.preferences['feedback__feedback_affects_adjudicator_scores'] = False
        self.tournament.preferences['data_entry__participant_feedback'] = 'private-urls'
        self.tournament.preferences['debate_rules__ballots_per_debate_prelim'] = 'per-debate'
        self.institution = Institution.objects.create(name='School', code='SCH')
        self.team = Team.objects.create(tournament=self.tournament, institution=self.institution, reference='A')
        self.other_team = Team.objects.create(tournament=self.tournament, institution=self.institution, reference='B')
        self.speaker = Speaker.objects.create(team=self.team, name='First Speaker', url_key='first-speaker')
        self.teammate = Speaker.objects.create(team=self.team, name='Second Speaker', url_key='second-speaker')
        self.other_speaker = Speaker.objects.create(team=self.other_team, name='Other Speaker', url_key='other-speaker')
        self.chair, self.panel, self.trainee = [
            Adjudicator.objects.create(
                tournament=self.tournament, institution=self.institution, name=name, base_score=3, url_key=key,
            ) for name, key in [('Chair Judge', 'chair'), ('Panel Judge', 'panel'), ('Trainee Judge', 'trainee')]
        ]
        self.round = Round.objects.create(
            tournament=self.tournament, seq=1, schedule_group=1, name='Round 1', abbreviation='R1',
            draw_status=Round.Status.RELEASED,
        )
        self.debate, self.dt = self._debate(self.round)

    def _debate(self, round, confirmed=True):
        debate = round.debate_set.create()
        dt = debate.debateteam_set.create(team=self.team, side=0)
        other_dt = debate.debateteam_set.create(team=self.other_team, side=1)
        for adj, position in [(self.chair, DebateAdjudicator.TYPE_CHAIR),
                              (self.panel, DebateAdjudicator.TYPE_PANEL),
                              (self.trainee, DebateAdjudicator.TYPE_TRAINEE)]:
            DebateAdjudicator.objects.create(debate=debate, adjudicator=adj, type=position)
        ballot = BallotSubmission.objects.create(debate=debate, confirmed=confirmed, submitter_type='T')
        for source, win in [(dt, True), (other_dt, False)]:
            TeamScore.objects.create(ballot_submission=ballot, debate_team=source, points=int(win), win=win, score=75)
        return debate, dt

    def _url(self, speaker=None):
        return reverse_tournament('privateurls-person-index', self.tournament, kwargs={
            'url_key': (speaker or self.speaker).url_key,
        })

    def _feedback_url(self, speaker=None):
        return reverse_tournament('adjfeedback-public-add-from-team-randomised', self.tournament, kwargs={
            'url_key': (speaker or self.speaker).url_key,
        })

    def _feedback(self, adj, confirmed=True, source=None):
        return AdjudicatorFeedback.objects.create(
            source_team=source or self.dt, adjudicator=adj, score=3, confirmed=confirmed, submitter_type='P',
        )

    def _items(self, response):
        return [item for group in response.context['missing_team_feedback_rounds'] for item in group['items']]

    def test_lists_voting_adjudicators_with_preselected_links(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="missing-team-feedback"')
        self.assertEqual(response.context['missing_team_feedback_count'], 2)
        items = self._items(response)
        self.assertEqual([item['target_names'] for item in items], [[self.chair.name], [self.panel.name]])
        for item, adj in zip(items, [self.chair, self.panel]):
            target = f'{self.debate.pk}-{adj.pk}'
            self.assertEqual(parse_qs(urlsplit(item['url']).query), {'target': [target]})
            form_response = self.client.get(item['url'])
            self.assertEqual(form_response.context['form']['target'].value(), target)

    def test_partial_submission_and_teammate_submission(self):
        self._feedback(self.chair)
        response = self.client.get(self._url())
        self.assertEqual(response.context['missing_team_feedback_count'], 1)
        self.assertEqual(self._items(response)[0]['target_names'], [self.panel.name])
        response = self.client.post(self._feedback_url(self.teammate), {'target': f'{self.debate.pk}-{self.panel.pk}'})
        self.assertEqual(response.status_code, 302)
        feedback = AdjudicatorFeedback.objects.get(source_team=self.dt, adjudicator=self.panel)
        self.assertTrue(feedback.confirmed)
        self.assertEqual(feedback.participant_submitter_id, self.teammate.pk)
        for speaker in [self.speaker, self.teammate]:
            response = self.client.get(self._url(speaker))
            self.assertEqual(response.context['missing_team_feedback_count'], 0)
            self.assertContains(response, 'No feedback is currently missing from your team.')

    def test_unconfirmed_and_other_team_submissions_do_not_fulfil(self):
        self._feedback(self.chair, confirmed=False)
        self._feedback(self.panel, source=self.debate.debateteam_set.get(team=self.other_team))
        response = self.client.get(self._url())
        self.assertEqual(response.context['missing_team_feedback_count'], 2)

    def test_duplicate_confirmed_submissions_are_not_missing(self):
        first = self._feedback(self.chair)
        self._feedback(self.chair)
        # Simulate historical duplicate confirmations, bypassing save's version handling.
        AdjudicatorFeedback.objects.filter(pk=first.pk).update(confirmed=True)
        response = self.client.get(self._url())
        self.assertEqual(self._items(response)[0]['target_names'], [self.panel.name])
        self.assertEqual(response.context['missing_team_feedback_count'], 1)

    def test_section_is_hidden_and_progress_skipped_when_disabled(self):
        self.tournament.preferences['feedback__show_missing_team_feedback'] = False
        with patch('privateurls.views.FeedbackProgressForTeam') as progress:
            response = self.client.get(self._url())
        progress.assert_not_called()
        self.assertNotContains(response, 'id="missing-team-feedback"')

    def test_section_is_hidden_when_private_feedback_or_team_feedback_disabled(self):
        for key, value in [('data_entry__participant_feedback', 'public'), ('feedback__feedback_from_teams', 'no-one')]:
            with self.subTest(preference=key):
                previous = self.tournament.preferences[key]
                self.tournament.preferences[key] = value
                with patch('privateurls.views.FeedbackProgressForTeam') as progress:
                    response = self.client.get(self._url())
                progress.assert_not_called()
                self.assertNotContains(response, 'id="missing-team-feedback"')
                self.tournament.preferences[key] = previous

    def test_adjudicator_page_does_not_calculate_team_progress(self):
        url = reverse_tournament('privateurls-person-index', self.tournament, kwargs={'url_key': self.chair.url_key})
        with patch('privateurls.views.FeedbackProgressForTeam') as progress:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        progress.assert_not_called()
        self.assertNotContains(response, 'id="missing-team-feedback"')

    def test_ineligible_rounds_are_excluded(self):
        for field, value in [('silent', True), ('draw_status', Round.Status.CONFIRMED),
                             ('draw_status', Round.Status.TEAMS_RELEASED), ('stage', Round.Stage.ELIMINATION)]:
            with self.subTest(field=field, value=value):
                previous = getattr(self.round, field)
                setattr(self.round, field, value)
                self.round.save()
                response = self.client.get(self._url())
                self.assertEqual(response.context['missing_team_feedback_count'], 0)
                response = self.client.get(self._feedback_url(), {'target': f'{self.debate.pk}-{self.chair.pk}'})
                self.assertIsNone(response.context['form']['target'].value())
                setattr(self.round, field, previous)
                self.round.save()
        BallotSubmission.objects.filter(debate=self.debate).update(confirmed=False)
        response = self.client.get(self._url())
        self.assertEqual(response.context['missing_team_feedback_count'], 0)

    def test_future_rounds_are_excluded_and_visible_rounds_sorted(self):
        future = Round.objects.create(
            tournament=self.tournament, seq=3, schedule_group=3, name='Future', abbreviation='F', draw_status=Round.Status.RELEASED,
        )
        self._debate(future)
        response = self.client.get(self._url())
        self.assertEqual(response.context['missing_team_feedback_count'], 2)
        middle = Round.objects.create(
            tournament=self.tournament, seq=2, schedule_group=2, name='Round 2', abbreviation='R2', draw_status=Round.Status.RELEASED,
        )
        self._debate(middle)
        self.round.completed = True
        self.round.save()
        response = self.client.get(self._url())
        self.assertEqual([group['round'].seq for group in response.context['missing_team_feedback_rounds']], [1, 2])

    def test_orallist_policy_is_one_obligation_with_acceptable_names(self):
        for policy in ['orallist', 'all-voting-adjs-allowed', 'all-adjs-allowed']:
            with self.subTest(policy=policy):
                self.tournament.preferences['feedback__feedback_from_teams'] = policy
                response = self.client.get(self._url())
                self.assertEqual(response.context['missing_team_feedback_count'], 1)
                item = self._items(response)[0]
                self.assertCountEqual(item['target_names'], [self.chair.name, self.panel.name])
                self.assertEqual(item['url'], self._feedback_url())
        self._feedback(self.panel)
        response = self.client.get(self._url())
        self.assertEqual(response.context['missing_team_feedback_count'], 0)

    def test_all_adjudicators_policy_includes_trainees(self):
        self.tournament.preferences['feedback__feedback_from_teams'] = 'all-adjs'
        response = self.client.get(self._url())
        self.assertEqual(response.context['missing_team_feedback_count'], 3)
        self.assertIn([self.trainee.name], [item['target_names'] for item in self._items(response)])

    def test_orallist_with_single_target_has_preselected_link(self):
        self.tournament.preferences['feedback__feedback_from_teams'] = 'orallist'
        self.debate.debateadjudicator_set.filter(adjudicator=self.panel).delete()
        response = self.client.get(self._url())
        self.assertEqual(response.context['missing_team_feedback_count'], 1)
        item = self._items(response)[0]
        self.assertEqual(item['target_names'], [self.chair.name])
        response = self.client.get(item['url'])
        self.assertEqual(response.context['form']['target'].value(), f'{self.debate.pk}-{self.chair.pk}')

    def test_one_team_jdl_debate(self):
        self.debate.debateteam_set.filter(team=self.other_team).delete()
        JDLFirstCategoryPreferences.save(self.tournament)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['missing_team_feedback_count'], 2)

    def test_invalid_preselection_is_ignored_and_post_remains_validated(self):
        invalid_targets = ['malformed', f'{self.debate.pk}-{self.trainee.pk}', '999999-999999']
        other_debate = self.round.debate_set.create()
        invalid_targets.append(f'{other_debate.pk}-{self.chair.pk}')
        for target in invalid_targets:
            with self.subTest(target=target):
                response = self.client.get(self._feedback_url(), {'target': target})
                self.assertIsNone(response.context['form']['target'].value())
                response = self.client.post(self._feedback_url(), {'target': target})
                self.assertIn('target', response.context['form'].errors)
        self.assertFalse(AdjudicatorFeedback.objects.exists())

    def test_query_preselection_does_not_override_post(self):
        response = self.client.post(
            self._feedback_url() + f'?target={self.debate.pk}-{self.chair.pk}',
            {'target': f'{self.debate.pk}-{self.panel.pk}'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(AdjudicatorFeedback.objects.get().adjudicator, self.panel)


class MissingTeamFeedbackPreferenceTests(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug='feedback-setting', name='Feedback Setting')

    def test_default_off_and_feedback_setting_can_be_saved(self):
        self.assertFalse(self.tournament.pref('show_missing_team_feedback'))
        form_class = tournament_preference_form_builder(self.tournament, section='feedback')
        form = form_class()
        key = 'feedback__show_missing_team_feedback'
        self.assertIn(key, form.fields)
        data = {name: form[name].value() for name in form.fields}
        data[key] = True
        form = form_class(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        form.update_preferences()
        self.assertTrue(Tournament.objects.get(pk=self.tournament.pk).pref('show_missing_team_feedback'))
        data[key] = False
        form = form_class(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        form.update_preferences()
        self.assertFalse(Tournament.objects.get(pk=self.tournament.pk).pref('show_missing_team_feedback'))

    def test_all_four_presets_enable_the_feature_and_expect_voting_adjudicators(self):
        for preset in [SDLFormatPreferences, JDLFirstCategoryPreferences, JDLFormatPreferences, NonLeagueTournamentsPreferences]:
            with self.subTest(preset=preset):
                self.tournament.preferences['feedback__show_missing_team_feedback'] = False
                preset.save(self.tournament)
                self.assertTrue(self.tournament.pref('show_missing_team_feedback'))
                self.assertEqual(self.tournament.pref('feedback_from_teams'), 'all-voting-adjs')
