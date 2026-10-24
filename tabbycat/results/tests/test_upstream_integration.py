from django.test import TestCase

from adjallocation.models import DebateAdjudicator
from draw.types import DebateSide
from importer.archive import Exporter, Importer
from participants.models import Adjudicator, Speaker, Team
from results.models import ScoreCriterion
from results.result import DebateResultByAdjudicatorWithScores

from .test_forms import BallotSetFormTestMixin


class MedianArchiveIntegrationTests(BallotSetFormTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        prefs = self.tournament.preferences
        prefs['debate_rules__ballots_per_debate_prelim'] = 'per-adj'
        prefs['debate_rules__substantive_speakers'] = 1
        prefs['debate_rules__reply_scores_enabled'] = True
        prefs['debate_rules__adjudicator_weighting'] = 'tabbycat-default'
        prefs['scoring__margin_includes_dissenters'] = True
        prefs['scoring__score_aggregation_function'] = 'median'
        prefs['data_entry__allow_self_split_ballots'] = True
        self.adjudicator.is_tester = True
        self.adjudicator.save()
        self.criterion = self.create_criterion(speech_type=ScoreCriterion.SpeechType.REPLY, weight=0.5)
        self.ballotsub.confirmed = True
        self.ballotsub.save()
        for team in Team.objects.filter(tournament=self.tournament):
            Speaker.objects.create(team=team, name=team.reference)

    def make_result(self, panel_size=1):
        judges = [self.adjudicator]
        if panel_size == 2:
            panel = Adjudicator.objects.create(tournament=self.tournament, name='Panel', base_score=5)
            DebateAdjudicator.objects.create(debate=self.debate, adjudicator=panel, type=DebateAdjudicator.TYPE_PANEL)
            judges.append(panel)
        result = DebateResultByAdjudicatorWithScores(self.ballotsub, criteria=[self.criterion])
        for side in (DebateSide.AFF, DebateSide.NEG):
            speaker = self.debate.get_dt(side).team.speaker_set.get()
            for position in self.tournament.positions:
                result.set_speaker(side, position, speaker)
            for index, judge in enumerate(judges):
                result.set_score(judge, side, 1, 74 + side + index)
                result.set_criterion_score(judge, side, 2, self.criterion, 30 + side + index)
        return result

    def test_reply_only_criteria_keep_substantive_scores_and_fractional_weights(self):
        result = self.make_result(panel_size=2)
        self.assertTrue(result.is_complete())
        self.assertEqual(result.speakerscore_field_score(DebateSide.AFF, 1), 75)
        self.assertEqual(result.speakercriterionscore_field_score(DebateSide.AFF, 2, self.criterion), 31)
        self.assertEqual(result.speakerscore_field_score(DebateSide.AFF, 2), 15.5)
        # Team totals keep the mean of complete judge scores, not rounded medians.
        self.assertEqual(result.teamscore_field_score(DebateSide.AFF), 89.75)

    def test_archive_preserves_self_split_tester_and_scoring_policy(self):
        self.ballotsub.self_split = True
        self.ballotsub.save()
        self.make_result().save()
        root = Exporter(self.tournament).create_all()
        root.set('short', 'median-archive-import')
        self.assertEqual(root.find('round/debate').get('self-split'), 'true')
        importer = Importer(root)
        importer.import_tournament()
        tournament = importer.tournament
        ballot = tournament.round_set.get().debate_set.get().confirmed_ballot
        self.assertTrue(ballot.self_split)
        self.assertTrue(tournament.adjudicator_set.get().is_tester)
        self.assertEqual(tournament.pref('score_aggregation_function'), 'median')
        self.assertTrue(tournament.pref('allow_self_split_ballots'))
        self.assertEqual(sorted(ballot.teamscore_set.values_list('votes_given', flat=True)), [1, 2])
        self.assertEqual(ballot.result.speakerscore_field_score(DebateSide.AFF, 1), 74)

    def test_legacy_archive_defaults_optional_flags_to_false(self):
        self.make_result().save()
        root = Exporter(self.tournament).create_all()
        root.set('short', 'legacy-flags-import')
        root.attrib.pop('score-aggregation-function')
        root.attrib.pop('allow-self-split-ballots')
        for adjudicator in root.findall('participants/adjudicator'):
            adjudicator.attrib.pop('tester')
        importer = Importer(root)
        importer.import_tournament()
        tournament = importer.tournament
        ballot = tournament.round_set.get().debate_set.get().confirmed_ballot
        self.assertFalse(ballot.self_split)
        self.assertFalse(tournament.adjudicator_set.get().is_tester)
        self.assertFalse(tournament.pref('allow_self_split_ballots'))
        self.assertEqual(tournament.pref('score_aggregation_function'), 'mean')

    def test_optional_criteria_do_not_erase_speaker_totals(self):
        self.criterion.required = False
        self.criterion.save()
        result = self.make_result()
        result.set_criterion_score(self.adjudicator, DebateSide.AFF, 2, self.criterion, None)
        self.assertTrue(result.is_complete())
        self.assertEqual(result.speakerscore_field_score(DebateSide.AFF, 1), 74)
        self.assertEqual(result.speakerscore_field_score(DebateSide.AFF, 2), 0)
        self.tournament.preferences['scoring__score_aggregation_function'] = 'mean'
        self.tournament._prefs.pop('score_aggregation_function', None)
        self.assertEqual(result.speakerscore_field_score(DebateSide.AFF, 1), 74)
        self.assertEqual(result.speakerscore_field_score(DebateSide.AFF, 2), 0)
