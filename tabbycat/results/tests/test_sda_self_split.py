from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from adjallocation.models import DebateAdjudicator
from api.serializers import BallotSerializer
from draw.types import DebateSide
from importer.archive import Exporter, Importer
from participants.models import Adjudicator, Speaker
from results.forms import PerAdjudicatorBallotSetForm, SingleBallotSetForm
from results.models import BallotSubmission
from results.result import DebateResultByAdjudicatorWithScores
from seasonbreaks.models import BreakLeague, BreakRegion, BreakSeason, BreakTournament
from seasonbreaks.services import freeze_break_tournament
from standings.speakers import SpeakerStandingsGenerator

from .test_forms import BallotSetFormTestMixin


class SDASelfSplitTests(BallotSetFormTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        for key, value in {
            'debate_rules__ballots_per_debate_prelim': 'per-adj',
            'debate_rules__substantive_speakers': 1,
            'debate_rules__reply_scores_enabled': False,
            'debate_rules__adjudicator_weighting': 'weighted-to-three',
            'scoring__margin_includes_dissenters': True,
            'data_entry__allow_self_split_ballots': True,
        }.items():
            self.tournament.preferences[key] = value
        self.ballotsub.submitter_type = BallotSubmission.Submitter.PUBLIC
        self.ballotsub.confirmed = True
        self.ballotsub.save()
        self.result = DebateResultByAdjudicatorWithScores(self.ballotsub)
        for side, mark in ((DebateSide.AFF, 76), (DebateSide.NEG, 74)):
            speaker = Speaker.objects.create(team=self.debate.get_dt(side).team, name=f'Speaker {side}')
            self.result.set_speaker(side, 1, speaker)
            self.result.set_score(self.adjudicator, side, 1, mark)
        self.result.save()

    def speaker_snapshot(self):
        return list(self.ballotsub.speakerscore_set.order_by('speaker_id').values_list('speaker_id', 'position', 'score'))

    def averages(self):
        generator = SpeakerStandingsGenerator(('average',), ('rank',), tournament=self.tournament)
        standings = generator.generate(Speaker.objects.filter(team__tournament=self.tournament), round=self.debate.round)
        return {info.instance_id: info.metrics['average'] for info in standings}

    def serializer(self, **data):
        user, _ = get_user_model().objects.get_or_create(username='split-admin', defaults={'is_superuser': True})
        request = RequestFactory().patch('/')
        request.user = user
        return BallotSerializer(instance=self.ballotsub, data=data, partial=True, context={
            'debate': self.debate, 'round': self.debate.round, 'tournament': self.tournament,
            'request': request, 'participant_requester': None,
        })

    def test_split_changes_votes_only_and_keeps_weighted_averages(self):
        before = self.speaker_snapshot()
        averages = self.averages()
        team_scores = list(self.ballotsub.teamscore_set.order_by('debate_team_id').values_list('score', 'points', 'win', 'margin'))
        self.assertEqual(sorted(self.ballotsub.teamscore_set.values_list('votes_given', flat=True)), [0, 3])
        self.ballotsub.self_split = True
        self.ballotsub.save()
        self.result.save()
        self.assertEqual(sorted(self.ballotsub.teamscore_set.values_list('votes_given', flat=True)), [1, 2])
        self.assertEqual(set(self.ballotsub.teamscore_set.values_list('votes_possible', flat=True)), {3})
        self.assertEqual(before, self.speaker_snapshot())
        self.assertEqual(averages, self.averages())
        self.assertEqual(team_scores, list(self.ballotsub.teamscore_set.order_by('debate_team_id').values_list('score', 'points', 'win', 'margin')))
        self.assertEqual(self.ballotsub.speakerscorebyadj_set.count(), 2)

    def test_both_ballot_forms_offer_sda_self_split(self):
        for form_class in (SingleBallotSetForm, PerAdjudicatorBallotSetForm):
            form = form_class(self.ballotsub, tabroom=True, filled=True, vetos={})
            self.assertIn('self_split', form.fields)

    def test_existing_sda_averages_keep_their_original_comparison_precision(self):
        score = self.ballotsub.speakerscore_set.first()
        score.score = 65.5
        score.save()
        self.assertEqual(self.averages()[score.speaker_id], 65.5 / 3)

    def test_api_toggle_recalculates_votes_without_changing_marks(self):
        before = self.speaker_snapshot()
        serializer = self.serializer(self_split=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.ballotsub.refresh_from_db()
        self.assertTrue(self.ballotsub.self_split)
        self.assertEqual(sorted(self.ballotsub.teamscore_set.values_list('votes_given', flat=True)), [1, 2])
        self.assertEqual(before, self.speaker_snapshot())
        serializer = self.serializer(self_split=False)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.assertEqual(sorted(self.ballotsub.teamscore_set.values_list('votes_given', flat=True)), [0, 3])

    def test_invalid_api_split_is_rejected_before_write(self):
        for option, value in (
            ('data_entry__allow_self_split_ballots', False),
            ('debate_rules__ballots_per_debate_prelim', 'per-debate'),
        ):
            old = self.tournament.preferences[option]
            self.tournament.preferences[option] = value
            self.tournament._prefs.clear()
            serializer = self.serializer(self_split=True)
            self.assertFalse(serializer.is_valid())
            self.assertIn('self_split', serializer.errors)
            self.tournament.preferences[option] = old
        self.tournament._prefs.clear()
        serializer = self.serializer(self_split=True, forfeit=True)
        self.assertFalse(serializer.is_valid())
        panel = Adjudicator.objects.create(tournament=self.tournament, name='Panel')
        DebateAdjudicator.objects.create(debate=self.debate, adjudicator=panel, type=DebateAdjudicator.TYPE_PANEL)
        del self.debate._adjudicators
        serializer = self.serializer(self_split=True)
        self.assertFalse(serializer.is_valid())
        self.ballotsub.refresh_from_db()
        self.assertFalse(self.ballotsub.self_split)

    def test_archive_round_trip_preserves_sda_split_and_weighting(self):
        self.ballotsub.self_split = True
        self.ballotsub.save()
        self.result.save()
        root = Exporter(self.tournament).create_all()
        root.set('short', 'sda-split-import')
        importer = Importer(root)
        importer.import_tournament()
        tournament = importer.tournament
        ballot = tournament.round_set.get().debate_set.get().confirmed_ballot
        self.assertEqual(tournament.pref('adjudicator_weighting'), 'weighted-to-three')
        self.assertTrue(ballot.self_split)
        self.assertEqual(sorted(ballot.teamscore_set.values_list('votes_given', flat=True)), [1, 2])
        self.assertEqual(sorted(ballot.speakerscore_set.values_list('score', flat=True)), [222, 228])

    def test_season_breaks_receive_two_and_one_votes(self):
        self.ballotsub.self_split = True
        self.ballotsub.save()
        self.result.save()
        league, _ = BreakLeague.objects.get_or_create(slug='sdl', defaults={'name': 'SDL'})
        season = BreakSeason.objects.create(name='Season', slug='season', league=league)
        region = BreakRegion.objects.create(name='West', season=season)
        tournament = BreakTournament.objects.create(season=season, region=region, tournament=self.tournament)
        freeze_break_tournament(tournament)
        self.assertEqual(sorted(tournament.team_results.values_list('ballots', flat=True)), [1, 2])
        self.assertEqual(sorted(tournament.team_results.values_list('wins', flat=True)), [0, 1])
