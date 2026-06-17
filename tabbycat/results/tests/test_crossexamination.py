"""Tests for the cross-examination scoring feature."""

import logging

from django.test import TestCase

from draw.models import Debate, DebateTeam
from draw.types import DebateSide
from participants.models import Institution, Speaker, Team
from results.models import BallotSubmission, CrossExamination
from results.result import ConsensusDebateResultWithScores
from tournaments.models import Round, Tournament
from utils.tests import suppress_logs
from venues.models import Venue


class TestCrossExaminationConsensus(TestCase):
    """End-to-end test that cross-examination scores are entered, saved,
    reloaded and folded into the team total for a consensus ballot."""

    SIDES = [DebateSide.AFF, DebateSide.NEG]
    NSPEAKERS = 3

    def setUp(self):
        self.tournament = Tournament.objects.create(slug="cxtest", name="CXTest")
        self.set_pref('debate_rules', 'teams_in_debate', 2)
        self.set_pref('debate_rules', 'substantive_speakers', self.NSPEAKERS)
        self.set_pref('debate_rules', 'reply_scores_enabled', False)
        self.set_pref('debate_rules', 'cross_examinations_enabled', True)

        self.teams = []
        for i in range(2):
            inst = Institution.objects.create(code="Inst{:d}".format(i), name="Institution {:d}".format(i))
            team = Team.objects.create(tournament=self.tournament, institution=inst,
                reference="Team {:d}".format(i), use_institution_prefix=False)
            self.teams.append(team)
            for j in range(self.NSPEAKERS):
                Speaker.objects.create(team=team, name="Speaker {:d}-{:d}".format(i, j))

        venue = Venue.objects.create(name="Venue", priority=10)
        rd = Round.objects.create(tournament=self.tournament, seq=1, abbreviation="R1")
        self.debate = Debate.objects.create(round=rd, venue=venue)
        for team, side in zip(self.teams, [0, 1]):
            DebateTeam.objects.create(debate=self.debate, team=team, side=side)

        self.crosses = [
            CrossExamination.objects.create(tournament=self.tournament, seq=1, name="1x2",
                weight=1.0, min_score=2, max_score=6, step=0.5, required=True),
            CrossExamination.objects.create(tournament=self.tournament, seq=2, name="2x1",
                weight=1.0, min_score=2, max_score=6, step=0.5, required=True),
        ]

    def set_pref(self, section, name, value):
        self.tournament.preferences[section + '__' + name] = value
        if name in self.tournament._prefs:
            del self.tournament._prefs[name]

    def _new_result(self, ballotsub):
        return ConsensusDebateResultWithScores(ballotsub, crosses=self.crosses, using_cross_examinations=True)

    def test_cross_scores_roundtrip_and_team_total(self):
        ballotsub = BallotSubmission.objects.create(debate=self.debate, confirmed=True,
            submitter_type=BallotSubmission.Submitter.TABROOM)
        result = self._new_result(ballotsub)

        for side, team in zip(self.SIDES, self.teams):
            for pos, speaker in enumerate(team.speaker_set.all()[0:self.NSPEAKERS], start=1):
                result.set_speaker(side, pos, speaker)
                result.set_score(side, pos, 75.0)

        # AFF crosses total 4 + 5 = 9; NEG crosses total 3 + 3 = 6
        result.set_cross_score(DebateSide.AFF, self.crosses[0], 4)
        result.set_cross_score(DebateSide.AFF, self.crosses[1], 5)
        result.set_cross_score(DebateSide.NEG, self.crosses[0], 3)
        result.set_cross_score(DebateSide.NEG, self.crosses[1], 3)

        self.assertTrue(result.is_complete())
        with suppress_logs('results.result', logging.WARNING):
            result.save()

        # Reload from the database and confirm everything round-trips.
        reloaded = self._new_result(BallotSubmission.objects.get(debate=self.debate, confirmed=True))

        self.assertEqual(reloaded.get_cross_score(DebateSide.AFF, self.crosses[0]), 4)
        self.assertEqual(reloaded.get_cross_score(DebateSide.AFF, self.crosses[1]), 5)
        self.assertEqual(reloaded.get_cross_total(DebateSide.AFF), 9)
        self.assertEqual(reloaded.get_cross_total(DebateSide.NEG), 6)

        speech_aff = sum(reloaded.get_score(DebateSide.AFF, p) for p in reloaded.positions)
        speech_neg = sum(reloaded.get_score(DebateSide.NEG, p) for p in reloaded.positions)
        self.assertEqual(speech_aff, 225)
        # Team total folds in the cross total.
        self.assertEqual(reloaded.teamscore_field_score(DebateSide.AFF), speech_aff + 9)
        self.assertEqual(reloaded.teamscore_field_score(DebateSide.NEG), speech_neg + 6)
        # AFF (234) beats NEG (231) on cross scores despite identical speeches.
        self.assertEqual(reloaded.winning_side(), DebateSide.AFF)

    def test_incomplete_when_required_cross_missing(self):
        ballotsub = BallotSubmission.objects.create(debate=self.debate, confirmed=True,
            submitter_type=BallotSubmission.Submitter.TABROOM)
        result = self._new_result(ballotsub)
        for side, team in zip(self.SIDES, self.teams):
            for pos, speaker in enumerate(team.speaker_set.all()[0:self.NSPEAKERS], start=1):
                result.set_speaker(side, pos, speaker)
                result.set_score(side, pos, 75.0)
        # Leave all cross scores blank -> required crosses make it incomplete.
        self.assertFalse(result.is_complete())
