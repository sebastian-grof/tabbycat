import logging

from django.test import TestCase

from adjallocation.models import DebateAdjudicator
from draw.models import Debate, DebateTeam
from draw.types import DebateSide
from participants.models import Adjudicator, Institution, Speaker, Team
from results.bye_scores import refresh_bye_ballots, refresh_forfeit_ballots, sync_forfeit_ballot
from results.models import BallotSubmission, CrossExaminationScore, SpeakerScore, TeamScore
from tournaments.models import Round, Tournament
from utils.tables import TabbycatTableBuilder
from utils.tests import suppress_logs
from venues.models import Venue

from ..base import StandingsError
from ..round_results import add_speaker_round_results
from ..speakers import SpeakerStandingsGenerator
from ..teams import TeamStandingsGenerator


class TestTrivialStandings(TestCase):
    """Tests cases with just two teams and two rounds.

    Mostly intended to check that it doesn't crash under lots of different
    configurations, rather than check the results of the ordering or aggregation
    functions themselves."""

    def setUp(self):
        self.tournament = Tournament.objects.create(slug="trivialstandingstest", name="Trivial standings test")
        self.team1 = Team.objects.create(tournament=self.tournament, reference="1", use_institution_prefix=False)
        self.team2 = Team.objects.create(tournament=self.tournament, reference="2", use_institution_prefix=False)
        adj = Adjudicator.objects.create(tournament=self.tournament, name="Adjudicator")
        for i in [1, 2]:
            rd = Round.objects.create(tournament=self.tournament, seq=i)
            debate = Debate.objects.create(round=rd, flags=['pullup'])
            dt1 = DebateTeam.objects.create(debate=debate, team=self.team1, side=DebateSide.AFF, flags=['pullup'])
            dt2 = DebateTeam.objects.create(debate=debate, team=self.team2, side=DebateSide.NEG)
            DebateAdjudicator.objects.create(debate=debate, adjudicator=adj, type=DebateAdjudicator.TYPE_CHAIR)
            ballotsub = BallotSubmission.objects.create(debate=debate, confirmed=True)
            TeamScore.objects.create(debate_team=dt1, ballot_submission=ballotsub,
                margin=+2*i, points=1, score=100+i, win=True,  votes_given=1, votes_possible=1)
            TeamScore.objects.create(debate_team=dt2, ballot_submission=ballotsub,
                margin=-2*i, points=0, score=100-i, win=False, votes_given=0, votes_possible=1)

    def tearDown(self):
        DebateTeam.objects.filter(team__tournament=self.tournament).delete()
        self.tournament.delete()

    def get_standings(self, generator):
        with suppress_logs('standings.metrics', logging.INFO):
            standings = generator.generate(self.tournament.team_set.all(), tournament=self.tournament)
        return standings

    def set_up_speaker_scores(self, position):
        speaker1 = Speaker.objects.create(team=self.team1, name="Speaker 1")
        speaker2 = Speaker.objects.create(team=self.team2, name="Speaker 2")
        for i in [1, 2]:
            rd = Round.objects.get(tournament=self.tournament, seq=i)
            dt1 = DebateTeam.objects.get(debate__round=rd, team=self.team1)
            dt2 = DebateTeam.objects.get(debate__round=rd, team=self.team2)
            ballotsub = BallotSubmission.objects.get(debate__round=rd)
            SpeakerScore.objects.create(debate_team=dt1, ballot_submission=ballotsub,
                speaker=speaker1, position=position, score=100+i)
            SpeakerScore.objects.create(debate_team=dt2, ballot_submission=ballotsub,
                speaker=speaker2, position=position, score=100-i)

    def _base_metric_test(self, metrics):
        generator = TeamStandingsGenerator(metrics.keys(), ())
        standings = self.get_standings(generator)
        for mkey, mvalues in metrics.items():
            if isinstance(mvalues, dict):
                key, values = next(iter(mvalues.items()))
            else:
                key, values = mkey, mvalues
            self.assertEqual(standings.get_standing(self.team1).metrics[key], values[0])
            self.assertEqual(standings.get_standing(self.team2).metrics[key], values[1])

    def test_nothing(self):
        # just test that it does not crash
        generator = TeamStandingsGenerator((), ())
        generator.generate(self.tournament.team_set.all(), tournament=self.tournament)

    def test_no_metrics(self):
        generator = TeamStandingsGenerator((), ('rank', 'subrank'))
        standings = self.get_standings(generator)
        self.assertEqual(standings.get_standing(self.team1).rankings['rank'], (1, True))
        self.assertEqual(standings.get_standing(self.team2).rankings['rank'], (1, True))
        self.assertEqual(standings.get_standing(self.team1).rankings['subrank'], (1, True))
        self.assertEqual(standings.get_standing(self.team2).rankings['subrank'], (1, True))

    def test_only_extra_metrics(self):
        generator = TeamStandingsGenerator((), ('rank', 'subrank'), extra_metrics=('points',))
        standings = self.get_standings(generator)
        self.assertEqual(standings.get_standing(self.team1).rankings['rank'], (1, True))
        self.assertEqual(standings.get_standing(self.team2).rankings['rank'], (1, True))
        self.assertEqual(standings.get_standing(self.team1).rankings['subrank'], (1, True))
        self.assertEqual(standings.get_standing(self.team2).rankings['subrank'], (1, True))

    def test_no_rankings(self):
        self._base_metric_test({'points': [2, 0]})

    def test_wins(self):
        self._base_metric_test({'wins': [2, 0]})

    def test_speaks_sum(self):
        self._base_metric_test({'speaks_sum': [203, 197]})

    def test_speaks_avg(self):
        self._base_metric_test({'speaks_avg': [101.5, 98.5]})

    def test_speaks_ind_avg(self):
        self.set_up_speaker_scores(1)
        self._base_metric_test({'speaks_ind_avg': [101.5, 98.5]})

    def test_speaks_stddev(self):
        self._base_metric_test({'speaks_stddev': [.5, .5]})

    def test_draw_strength(self):
        # losing team has faced winning team twice, so draw strength is 2 * 2 = 4
        self._base_metric_test({'draw_strength': [0, 4]})

    def test_draw_strength_speaks(self):
        # teams have faced each other twice, so draw strength is twice opponent's score
        self._base_metric_test({'draw_strength_speaks': [394, 406]})

    def test_margin_sum(self):
        self._base_metric_test({'margin_sum': [6, -6]})

    def test_margin_avg(self):
        self._base_metric_test({'margin_avg': [3, -3]})

    def test_num_adjs(self):
        # normalized to 3 adjs per debate, so the winning team has 6 adjudicators
        self._base_metric_test({'num_adjs': [6, 0]})

    def test_wbw_not_tied(self):
        self._base_metric_test({'points': [2, 0], 'wbw': {'wbw1': ['n/a', 'n/a']}})

    def test_wbw_first(self):
        # tests wbw when it appears as the first metric
        self._base_metric_test({'wbw': {'wbw1': [2, 0]}})

    def test_wbw_tied(self):
        # firsts should be 0 for both teams as only applicable in BP, so is a tied
        # first metric, allowing wbw to be tested as a second metric (the normal use case)
        self._base_metric_test({'firsts': [0, 0], 'wbw': {'wbw1': [2, 0]}})

    def test_npullups(self):
        self._base_metric_test({'npullups': [2, 0]})

    def test_pullup_debates(self):
        self._base_metric_test({'pullup_debates': [2, 2]})

    def test_pullup_debates_combinable(self):
        self._base_metric_test({'points': [2, 0], 'npullups': [2, 0], 'pullup_debates': [2, 2]})

    def test_points_ranked(self):
        generator = TeamStandingsGenerator(('points',), ('rank',))
        standings = self.get_standings(generator)
        self.assertEqual(standings.get_standing(self.team1).metrics['points'], 2)
        self.assertEqual(standings.get_standing(self.team2).metrics['points'], 0)
        self.assertEqual(standings.get_standing(self.team1).rankings['rank'], (1, False))
        self.assertEqual(standings.get_standing(self.team2).rankings['rank'], (2, False))

    def test_speaks_ranked(self):
        generator = TeamStandingsGenerator(('speaks_sum',), ('rank',))
        standings = self.get_standings(generator)
        self.assertEqual(standings.get_standing(self.team1).metrics['speaks_sum'], 203)
        self.assertEqual(standings.get_standing(self.team2).metrics['speaks_sum'], 197)
        self.assertEqual(standings.get_standing(self.team1).rankings['rank'], (1, False))
        self.assertEqual(standings.get_standing(self.team2).rankings['rank'], (2, False))

    def test_points_speaks_subrank(self):
        generator = TeamStandingsGenerator(('points', 'speaks_sum'), ('rank', 'subrank'))
        standings = self.get_standings(generator)
        self.assertEqual(standings.get_standing(self.team1).metrics['points'], 2)
        self.assertEqual(standings.get_standing(self.team2).metrics['points'], 0)
        self.assertEqual(standings.get_standing(self.team1).metrics['speaks_sum'], 203)
        self.assertEqual(standings.get_standing(self.team2).metrics['speaks_sum'], 197)
        self.assertEqual(standings.get_standing(self.team1).rankings['rank'], (1, False))
        self.assertEqual(standings.get_standing(self.team2).rankings['rank'], (2, False))
        self.assertEqual(standings.get_standing(self.team1).rankings['subrank'], (1, False))
        self.assertEqual(standings.get_standing(self.team2).rankings['subrank'], (1, False))

    def test_double_metric_error(self):
        self.assertRaises(StandingsError, TeamStandingsGenerator, ('points', 'wbw', 'points'), ('rank',))

    def test_points_with_extra_team(self):
        # check that a team with no debates doesn't throw off the rankings
        team_extra = Team.objects.create(tournament=self.tournament, reference="extra", use_institution_prefix=False)
        generator = TeamStandingsGenerator(('points',), ('rank',))
        standings = self.get_standings(generator)
        self.assertEqual(standings.get_standing(self.team1).rankings['rank'], (1, False))
        self.assertEqual(standings.get_standing(self.team2).rankings['rank'], (2, False))
        self.assertEqual(standings.get_standing(team_extra).rankings['rank'], (3, False))

    def test_wins_with_extra_team(self):
        # check that a team with no debates doesn't throw off the rankings
        team_extra = Team.objects.create(tournament=self.tournament, reference="extra", use_institution_prefix=False)
        generator = TeamStandingsGenerator(('wins',), ('rank',))
        standings = self.get_standings(generator)
        self.assertEqual(standings.get_standing(self.team1).rankings['rank'], (1, False))
        self.assertEqual(standings.get_standing(self.team2).rankings['rank'], (2, True))
        self.assertEqual(standings.get_standing(team_extra).rankings['rank'], (2, True))

    def test_noncombinable_metric(self):
        # Check that metrics that add a join do not interfere with other metrics
        self.set_up_speaker_scores(1)
        self.set_up_speaker_scores(2)
        self._base_metric_test({'wins': [2, 0], 'speaks_ind_avg': [101.5, 98.5]})


class IgnorableDebateMixin:

    def set_up_ignorable_debate(self):
        adj = Adjudicator.objects.get()
        rd = Round.objects.create(tournament=self.tournament, seq=3)
        debate = Debate.objects.create(round=rd)
        dt1 = DebateTeam.objects.create(debate=debate, team=self.team1, side=DebateSide.AFF)
        dt2 = DebateTeam.objects.create(debate=debate, team=self.team2, side=DebateSide.NEG)
        DebateAdjudicator.objects.create(debate=debate, adjudicator=adj, type=DebateAdjudicator.TYPE_CHAIR)
        ballotsub = BallotSubmission.objects.create(debate=debate, confirmed=True)
        TeamScore.objects.create(debate_team=dt1, ballot_submission=ballotsub,
            margin=-25, points=0, score=300, win=False, votes_given=0, votes_possible=3)
        TeamScore.objects.create(debate_team=dt2, ballot_submission=ballotsub,
            margin=+25, points=1, score=325, win=True,  votes_given=3, votes_possible=3)
        return debate

    def set_up_speaker_scores(self, position):
        super().set_up_speaker_scores(position)
        speaker1 = Speaker.objects.filter(team=self.team1, name="Speaker 1").first()
        speaker2 = Speaker.objects.filter(team=self.team2, name="Speaker 2").first()
        rd = Round.objects.get(tournament=self.tournament, seq=3)
        dt1 = DebateTeam.objects.get(debate__round=rd, team=self.team1)
        dt2 = DebateTeam.objects.get(debate__round=rd, team=self.team2)
        ballotsub = BallotSubmission.objects.get(debate__round=rd)
        SpeakerScore.objects.create(debate_team=dt1, ballot_submission=ballotsub,
            speaker=speaker1, position=position, score=350)
        SpeakerScore.objects.create(debate_team=dt2, ballot_submission=ballotsub,
            speaker=speaker2, position=position, score=375)


class TestStandingsWithEliminationRound(IgnorableDebateMixin, TestTrivialStandings):

    def setUp(self):
        super().setUp()
        debate = self.set_up_ignorable_debate()
        debate.round.stage = Round.Stage.ELIMINATION
        debate.round.save()


class TestStandingsWithUnconfirmedBallotSubmission(IgnorableDebateMixin, TestTrivialStandings):

    def setUp(self):
        super().setUp()
        debate = self.set_up_ignorable_debate()
        debate.ballotsubmission_set.update(confirmed=False)

    def test_draw_strength(self):
        # The ignorable debate still counts as an opponent (because they definitely faced each
        # other) but does not count as a win (because it's unconfirmed). So the losing team has
        # faced the winning team 3 times (including ignorable debate), and the winning team has 2
        # wins (excluding ignorable debate), for a losing team draw strength of 3 * 2 = 6.
        self._base_metric_test({'draw_strength': [0, 6]})

    def test_draw_strength_speaks(self):
        self._base_metric_test({'draw_strength_speaks': [591, 609]})


class TestBasicStandings(TestCase):

    TEAMS = "ABCD"

    testdata = dict()
    testdata[1] = \
        {'rankings': {('points', 'speaks_sum'): ['A', 'D', 'C', 'B'],
                      ('points', 'speaks_sum', 'draw_strength', 'margin_sum'): ['A', 'D', 'C', 'B']},
         'standings': {'A': {'against': {'B': 2, 'C': 0, 'D': 'n/a'},
                             'draw_strength': 2,
                             'margin_sum': 46.0,
                             'points': 2,
                             'speaks_sum': 804.5},
                       'B': {'against': {'A': 0, 'C': 'n/a', 'D': 0},
                             'draw_strength': 6,
                             'margin_sum': -62.0,
                             'points': 0,
                             'speaks_sum': 753.5},
                       'C': {'against': {'A': 1, 'B': 'n/a', 'D': 1},
                             'draw_strength': 6,
                             'margin_sum': 8.0,
                             'points': 2,
                             'speaks_sum': 784.5},
                       'D': {'against': {'A': 'n/a', 'B': 1, 'C': 1},
                             'draw_strength': 4,
                             'margin_sum': 8.0,
                             'points': 2,
                             'speaks_sum': 787.5}},
         'teams': ['A', 'B', 'C', 'D'],
         'teamscores': [{'AB': {'A': {'margin': 22.5,  'points': 1, 'score': 265.0, 'win': True,  'votes_given': 1, 'votes_possible': 1},
                                'B': {'margin': -22.5, 'points': 0, 'score': 242.5, 'win': False, 'votes_given': 0, 'votes_possible': 1}},
                         'CD': {'C': {'margin': 20.0,  'points': 1, 'score': 273.0, 'win': True,  'votes_given': 1, 'votes_possible': 1},
                                'D': {'margin': -20.0, 'points': 0, 'score': 253.0, 'win': False, 'votes_given': 0, 'votes_possible': 1}}},
                        {'AC': {'A': {'margin': -1.5,  'points': 0, 'score': 263.5, 'win': False, 'votes_given': 0, 'votes_possible': 1},
                                'C': {'margin': 1.5,   'points': 1, 'score': 265.0, 'win': True,  'votes_given': 1, 'votes_possible': 1}},
                         'BD': {'B': {'margin': -14.5, 'points': 0, 'score': 260.0, 'win': False, 'votes_given': 0, 'votes_possible': 1},
                                'D': {'margin': 14.5,  'points': 1, 'score': 274.5, 'win': True,  'votes_given': 1, 'votes_possible': 1}}},
                        {'AB': {'A': {'margin': 25.0,  'points': 1, 'score': 276.0, 'win': True,  'votes_given': 1, 'votes_possible': 1},
                                'B': {'margin': -25.0, 'points': 0, 'score': 251.0, 'win': False, 'votes_given': 0, 'votes_possible': 1}},
                         'CD': {'C': {'margin': -13.5, 'points': 0, 'score': 246.5, 'win': False, 'votes_given': 0, 'votes_possible': 1},
                                'D': {'margin': 13.5,  'points': 1, 'score': 260.0, 'win': True,  'votes_given': 1, 'votes_possible': 1}}}]}

    rankings = ('rank',)

    def setup_testdata(self, testdata):
        tournament = Tournament.objects.create(slug="basicstandingstest", name="Basic standings test")
        teams = dict()
        for team_name in testdata["teams"]:
            inst = Institution.objects.create(code=team_name, name=team_name)
            team = Team.objects.create(tournament=tournament, institution=inst, reference=team_name, use_institution_prefix=False)
            teams[team_name] = team
        inst = Institution.objects.create(code="Adjs", name="Adjudicators")
        for i in range(len(testdata["teams"])//2):
            Adjudicator.objects.create(tournament=tournament, institution=inst, name="Adjudicator {:d}".format(i), base_score=5)
            Venue.objects.create(name="Venue {:d}".format(i), priority=10)
        adjs = list(Adjudicator.objects.all())
        venues = list(Venue.objects.all())
        sides = [DebateSide.AFF, DebateSide.NEG]

        for r, debatedict in enumerate(testdata["teamscores"]):
            rd = Round.objects.create(tournament=tournament, seq=r, abbreviation="R{:d}".format(r))
            for adj, venue, (teamnames, teamscores) in zip(adjs, venues, debatedict.items()):
                debate = Debate.objects.create(round=rd, venue=venue)
                for team, side in zip(teamnames, sides):
                    DebateTeam.objects.create(debate=debate, team=teams[team], side=side)
                DebateAdjudicator.objects.create(debate=debate, adjudicator=adj, type=DebateAdjudicator.TYPE_CHAIR)
                ballotsub = BallotSubmission.objects.create(debate=debate, confirmed=True)
                for team, teamscore_dict in teamscores.items():
                    dt = DebateTeam.objects.get(debate=debate, team=teams[team])
                    TeamScore.objects.create(debate_team=dt, ballot_submission=ballotsub, **teamscore_dict)

        return tournament, teams

    def teardown_testdata(self, tournament):
        tournament.delete()

    def test_standings(self):
        for index, testdata in self.testdata.items():
            tournament, teams = self.setup_testdata(testdata)
            for metrics in testdata["rankings"].keys():
                with self.subTest(index=index, metrics=metrics):
                    generator = TeamStandingsGenerator(metrics, self.rankings)
                    with suppress_logs('standings.teams', logging.INFO), \
                            suppress_logs('standings.metrics', logging.INFO):
                        standings = generator.generate(tournament.team_set.all(), tournament=tournament)

                    self.assertEqual(len(standings), len(testdata["standings"]))
                    self.assertEqual(standings.metric_keys, list(metrics))

                    for teamname, expected in testdata["standings"].items():
                        team = teams[teamname]
                        standing = standings.get_standing(team)
                        for metric in metrics:
                            self.assertEqual(standing.metrics[metric], expected[metric])

                    ranked_teams = [teams[x] for x in testdata["rankings"][metrics]]
                    self.assertEqual(ranked_teams, standings.get_instance_list())

    # TODO check that WBW is correct when not in first metrics
    # TODO check that it doesn't break when not all metrics present
    # TODO check that it works for different rounds


class TestMissingStandings(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug="missingstandingstest", name="Missing standings test")
        self.team1 = Team.objects.create(tournament=self.tournament, reference="1", use_institution_prefix=False)
        self.team2 = Team.objects.create(tournament=self.tournament, reference="2", use_institution_prefix=False)

    def tearDown(self):
        self.tournament.delete()

    def get_standings(self, generator):
        with suppress_logs('standings.metrics', logging.INFO):
            return generator.generate(self.tournament.team_set.all(), tournament=self.tournament)

    def test_num_adjs_missing(self):
        generator = TeamStandingsGenerator(('num_adjs',), ())
        standings = self.get_standings(generator)
        self.assertEqual(standings.get_standing(self.team1).metrics['num_adjs'], 0)
        self.assertEqual(standings.get_standing(self.team2).metrics['num_adjs'], 0)


class TestSpeakerStandingsAverageMetric(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug="speakerstandingstest", name="Speaker standings test")
        self.team1 = Team.objects.create(tournament=self.tournament, reference="1", use_institution_prefix=False)
        self.team2 = Team.objects.create(tournament=self.tournament, reference="2", use_institution_prefix=False)
        self.speaker1 = Speaker.objects.create(team=self.team1, name="Speaker 1")
        self.speaker2 = Speaker.objects.create(team=self.team2, name="Speaker 2")

    def tearDown(self):
        self.tournament.delete()

    def set_tournament_preference(self, section, name, value):
        self.tournament.preferences[section + '__' + name] = value
        if name in self.tournament._prefs:
            del self.tournament._prefs[name]

    def add_round_scores(self, seq, team1_score, team2_score, team1_votes, team2_votes, votes_possible=3):
        rd = Round.objects.create(tournament=self.tournament, seq=seq)
        debate = Debate.objects.create(round=rd)
        dt1 = DebateTeam.objects.create(debate=debate, team=self.team1, side=DebateSide.AFF)
        dt2 = DebateTeam.objects.create(debate=debate, team=self.team2, side=DebateSide.NEG)
        ballotsub = BallotSubmission.objects.create(debate=debate, confirmed=True)
        TeamScore.objects.create(
            debate_team=dt1, ballot_submission=ballotsub, points=1, win=True, score=team1_score,
            votes_given=team1_votes, votes_possible=votes_possible,
        )
        TeamScore.objects.create(
            debate_team=dt2, ballot_submission=ballotsub, points=0, win=False, score=team2_score,
            votes_given=team2_votes, votes_possible=votes_possible,
        )
        SpeakerScore.objects.create(
            debate_team=dt1, ballot_submission=ballotsub, speaker=self.speaker1, position=1, score=team1_score,
        )
        SpeakerScore.objects.create(
            debate_team=dt2, ballot_submission=ballotsub, speaker=self.speaker2, position=1, score=team2_score,
        )

    def get_standings(self):
        generator = SpeakerStandingsGenerator(('average', 'total'), ())
        with suppress_logs('standings.metrics', logging.INFO):
            return generator.generate(Speaker.objects.filter(team__tournament=self.tournament), tournament=self.tournament, round=self.tournament.round_set.order_by('seq').last())

    def test_average_normalizes_by_votes_possible_when_dissenters_are_included(self):
        self.set_tournament_preference('debate_rules', 'adjudicator_weighting', 'weighted-to-three')
        self.set_tournament_preference('scoring', 'margin_includes_dissenters', True)
        self.add_round_scores(1, 60, 45, 3, 0)
        self.add_round_scores(2, 72, 63, 2, 1)

        standings = self.get_standings()

        self.assertAlmostEqual(22, standings.get_standing(self.speaker1).metrics['average'])
        self.assertAlmostEqual(18, standings.get_standing(self.speaker2).metrics['average'])
        self.assertAlmostEqual(132, standings.get_standing(self.speaker1).metrics['total'])
        self.assertAlmostEqual(108, standings.get_standing(self.speaker2).metrics['total'])

    def test_average_normalizes_by_votes_possible_when_dissenters_are_excluded(self):
        self.set_tournament_preference('debate_rules', 'adjudicator_weighting', 'weighted-to-three')
        self.set_tournament_preference('scoring', 'margin_includes_dissenters', False)
        self.add_round_scores(1, 40, 36, 2, 1)
        self.add_round_scores(2, 50, 42, 2, 1)

        standings = self.get_standings()

        self.assertAlmostEqual(15, standings.get_standing(self.speaker1).metrics['average'])
        self.assertAlmostEqual(13, standings.get_standing(self.speaker2).metrics['average'])
        self.assertAlmostEqual(90, standings.get_standing(self.speaker1).metrics['total'])
        self.assertAlmostEqual(78, standings.get_standing(self.speaker2).metrics['total'])

    def test_round_scores_normalize_by_votes_possible_when_weighted_to_three(self):
        self.set_tournament_preference('debate_rules', 'adjudicator_weighting', 'weighted-to-three')
        self.add_round_scores(1, 72, 63, 2, 1)

        standings = self.get_standings()
        add_speaker_round_results(standings, self.tournament.round_set.order_by('seq'), self.tournament)

        self.assertAlmostEqual(24, standings.get_standing(self.speaker1).scores[0])
        self.assertAlmostEqual(21, standings.get_standing(self.speaker2).scores[0])

    def test_round_scores_remain_raw_when_not_weighted_to_three(self):
        self.set_tournament_preference('debate_rules', 'adjudicator_weighting', 'tabbycat-default')
        self.add_round_scores(1, 72, 63, 2, 1)

        standings = self.get_standings()
        add_speaker_round_results(standings, self.tournament.round_set.order_by('seq'), self.tournament)

        self.assertAlmostEqual(72, standings.get_standing(self.speaker1).scores[0])
        self.assertAlmostEqual(63, standings.get_standing(self.speaker2).scores[0])


class TestByeAverageScores(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug="byeaveragestest", name="Bye averages test")
        self.tournament.preferences['draw_rules__bye_team_results'] = 'average'
        self.tournament.preferences['debate_rules__ballots_per_debate_prelim'] = 'per-adj'
        self.tournament.preferences['debate_rules__cross_examinations_enabled'] = True
        for key in ('bye_team_results', 'ballots_per_debate_prelim', 'cross_examinations_enabled'):
            self.tournament._prefs.pop(key, None)

        self.team1 = Team.objects.create(tournament=self.tournament, reference="1", use_institution_prefix=False)
        self.team2 = Team.objects.create(tournament=self.tournament, reference="2", use_institution_prefix=False)
        self.team3 = Team.objects.create(tournament=self.tournament, reference="3", use_institution_prefix=False)

        self.team1_speakers = [Speaker.objects.create(team=self.team1, name=f"Team 1 Speaker {i}") for i in range(1, 4)]
        self.team2_speakers = [Speaker.objects.create(team=self.team2, name=f"Team 2 Speaker {i}") for i in range(1, 4)]
        self.team3_speakers = [Speaker.objects.create(team=self.team3, name=f"Team 3 Speaker {i}") for i in range(1, 4)]

    def tearDown(self):
        self.tournament.delete()

    def _add_real_debate(self, seq, aff_team, neg_team, aff_speakers, neg_speakers, aff_scores, neg_scores, aff_total, neg_total):
        rd = Round.objects.create(tournament=self.tournament, seq=seq)
        debate = Debate.objects.create(round=rd)
        aff_dt = DebateTeam.objects.create(debate=debate, team=aff_team, side=DebateSide.AFF)
        neg_dt = DebateTeam.objects.create(debate=debate, team=neg_team, side=DebateSide.NEG)
        ballotsub = BallotSubmission.objects.create(debate=debate, confirmed=True)

        TeamScore.objects.create(
            debate_team=aff_dt, ballot_submission=ballotsub, points=1, win=True, score=aff_total,
            votes_given=3, votes_possible=3, margin=1,
        )
        TeamScore.objects.create(
            debate_team=neg_dt, ballot_submission=ballotsub, points=0, win=False, score=neg_total,
            votes_given=0, votes_possible=3, margin=-1,
        )

        for position, score in aff_scores.items():
            speaker = aff_speakers[0] if position == self.tournament.reply_position else aff_speakers[position - 1]
            SpeakerScore.objects.create(
                debate_team=aff_dt, ballot_submission=ballotsub, speaker=speaker, position=position, score=score,
            )

        for position, score in neg_scores.items():
            speaker = neg_speakers[0] if position == self.tournament.reply_position else neg_speakers[position - 1]
            SpeakerScore.objects.create(
                debate_team=neg_dt, ballot_submission=ballotsub, speaker=speaker, position=position, score=score,
            )

        return debate, aff_dt, neg_dt

    def _add_bye_debate(self, seq, team):
        rd = Round.objects.create(tournament=self.tournament, seq=seq)
        debate = Debate.objects.create(round=rd)
        return debate, DebateTeam.objects.create(debate=debate, team=team, side=DebateSide.BYE)

    def _add_forfeit_debate(self, seq, aff_team, neg_team, forfeiting_side):
        rd = Round.objects.create(tournament=self.tournament, seq=seq)
        debate = Debate.objects.create(round=rd)
        aff_dt = DebateTeam.objects.create(debate=debate, team=aff_team, side=DebateSide.AFF)
        neg_dt = DebateTeam.objects.create(debate=debate, team=neg_team, side=DebateSide.NEG)
        ballotsub = BallotSubmission.objects.create(debate=debate, confirmed=True, forfeit=True)
        sync_forfeit_ballot(ballotsub, forfeiting_side)
        return debate, ballotsub, aff_dt, neg_dt

    def test_first_round_bye_uses_global_defaults(self):
        debate, bye_dt = self._add_bye_debate(1, self.team1)

        refresh_bye_ballots(self.tournament)

        ballotsub = debate.ballotsubmission_set.get(confirmed=True)
        teamscore = TeamScore.objects.get(ballot_submission=ballotsub, debate_team=bye_dt)
        speakers = {
            ss.position: ss.score
            for ss in SpeakerScore.objects.filter(ballot_submission=ballotsub, debate_team=bye_dt)
        }

        self.assertEqual(276, teamscore.score)
        self.assertEqual(3, teamscore.votes_given)
        self.assertEqual(3, teamscore.votes_possible)
        self.assertEqual(60, speakers[1])
        self.assertEqual(60, speakers[2])
        self.assertEqual(60, speakers[3])
        self.assertEqual(48, speakers[self.tournament.reply_position])

    def test_bye_scores_refresh_after_later_real_debates(self):
        self._add_real_debate(
            1,
            self.team1,
            self.team2,
            self.team1_speakers,
            self.team2_speakers,
            {1: 60, 2: 57, 3: 54, 4: 48},
            {1: 54, 2: 51, 3: 48, 4: 45},
            267,
            246,
        )
        bye_debate, bye_dt = self._add_bye_debate(2, self.team1)

        refresh_bye_ballots(self.tournament)

        ballotsub = bye_debate.ballotsubmission_set.get(confirmed=True)
        self.assertEqual(267, TeamScore.objects.get(ballot_submission=ballotsub, debate_team=bye_dt).score)
        self.assertEqual(60, SpeakerScore.objects.get(ballot_submission=ballotsub, debate_team=bye_dt, position=1).score)

        self._add_real_debate(
            3,
            self.team1,
            self.team3,
            self.team1_speakers,
            self.team3_speakers,
            {1: 63, 2: 60, 3: 57, 4: 45},
            {1: 57, 2: 54, 3: 51, 4: 48},
            276,
            258,
        )

        refresh_bye_ballots(self.tournament)

        bye_teamscore = TeamScore.objects.get(ballot_submission=ballotsub, debate_team=bye_dt)
        bye_pos1 = SpeakerScore.objects.get(ballot_submission=ballotsub, debate_team=bye_dt, position=1)

        self.assertEqual(271.5, bye_teamscore.score)
        self.assertEqual(61.5, bye_pos1.score)

        standings_generator = SpeakerStandingsGenerator(('average', 'total'), ())
        with suppress_logs('standings.metrics', logging.INFO):
            standings = standings_generator.generate(
                Speaker.objects.filter(team__tournament=self.tournament),
                tournament=self.tournament,
                round=self.tournament.round_set.order_by('seq').last(),
            )

        speaker_standing = standings.get_standing(self.team1_speakers[0])
        self.assertAlmostEqual(20.5, speaker_standing.metrics['average'])
        self.assertAlmostEqual(184.5, speaker_standing.metrics['total'])

    def test_first_round_forfeit_awards_bye_style_scores_and_zeroes_loser(self):
        _, ballotsub, aff_dt, neg_dt = self._add_forfeit_debate(1, self.team1, self.team2, DebateSide.NEG)

        winner_score = TeamScore.objects.get(ballot_submission=ballotsub, debate_team=aff_dt)
        loser_score = TeamScore.objects.get(ballot_submission=ballotsub, debate_team=neg_dt)
        winner_speakers = {
            ss.position: ss.score
            for ss in SpeakerScore.objects.filter(ballot_submission=ballotsub, debate_team=aff_dt)
        }
        loser_speakers = {
            ss.position: ss.score
            for ss in SpeakerScore.objects.filter(ballot_submission=ballotsub, debate_team=neg_dt)
        }
        winner_cross_total = sum(
            float(score)
            for score in (
                CrossExaminationScore.objects
                .filter(ballot_submission=ballotsub, debate_team=aff_dt)
                .values_list('score', flat=True)
            )
        )
        loser_cross_total = sum(
            float(score)
            for score in (
                CrossExaminationScore.objects
                .filter(ballot_submission=ballotsub, debate_team=neg_dt)
                .values_list('score', flat=True)
            )
        )

        self.assertEqual(276, winner_score.score)
        self.assertEqual(3, winner_score.votes_given)
        self.assertEqual(3, winner_score.votes_possible)
        self.assertTrue(winner_score.win)
        self.assertEqual(60, winner_speakers[1])
        self.assertEqual(60, winner_speakers[2])
        self.assertEqual(60, winner_speakers[3])
        self.assertEqual(48, winner_speakers[self.tournament.reply_position])
        self.assertEqual(48, winner_cross_total)

        self.assertEqual(0, loser_score.score)
        self.assertEqual(0, loser_score.votes_given)
        self.assertEqual(3, loser_score.votes_possible)
        self.assertFalse(loser_score.win)
        self.assertTrue(all(score == 0 for score in loser_speakers.values()))
        self.assertEqual(0, loser_cross_total)

    def test_forfeit_winner_uses_running_average_and_loser_counts_zeroes(self):
        self._add_real_debate(
            1,
            self.team1,
            self.team2,
            self.team1_speakers,
            self.team2_speakers,
            {1: 60, 2: 57, 3: 54, 4: 48},
            {1: 54, 2: 51, 3: 48, 4: 45},
            267,
            246,
        )
        _, ballotsub, aff_dt, neg_dt = self._add_forfeit_debate(2, self.team1, self.team3, DebateSide.NEG)

        winner_score = TeamScore.objects.get(ballot_submission=ballotsub, debate_team=aff_dt)
        loser_score = TeamScore.objects.get(ballot_submission=ballotsub, debate_team=neg_dt)

        self.assertEqual(267, winner_score.score)
        self.assertEqual(0, loser_score.score)
        self.assertEqual(60, SpeakerScore.objects.get(ballot_submission=ballotsub, debate_team=aff_dt, position=1).score)
        self.assertEqual(0, SpeakerScore.objects.get(ballot_submission=ballotsub, debate_team=neg_dt, position=1).score)

        standings_generator = SpeakerStandingsGenerator(('average', 'total'), ())
        with suppress_logs('standings.metrics', logging.INFO):
            standings = standings_generator.generate(
                Speaker.objects.filter(team__tournament=self.tournament),
                tournament=self.tournament,
                round=self.tournament.round_set.order_by('seq').last(),
            )

        winner_standing = standings.get_standing(self.team1_speakers[0])
        loser_standing = standings.get_standing(self.team3_speakers[0])
        self.assertAlmostEqual(20, winner_standing.metrics['average'])
        self.assertAlmostEqual(120, winner_standing.metrics['total'])
        self.assertAlmostEqual(0, loser_standing.metrics['average'])
        self.assertAlmostEqual(0, loser_standing.metrics['total'])

    def test_forfeit_scores_refresh_after_later_real_debates(self):
        self._add_real_debate(
            1,
            self.team1,
            self.team2,
            self.team1_speakers,
            self.team2_speakers,
            {1: 60, 2: 57, 3: 54, 4: 48},
            {1: 54, 2: 51, 3: 48, 4: 45},
            267,
            246,
        )
        _, ballotsub, aff_dt, neg_dt = self._add_forfeit_debate(2, self.team1, self.team3, DebateSide.NEG)

        self.assertEqual(267, TeamScore.objects.get(ballot_submission=ballotsub, debate_team=aff_dt).score)
        self.assertEqual(60, SpeakerScore.objects.get(ballot_submission=ballotsub, debate_team=aff_dt, position=1).score)

        self._add_real_debate(
            3,
            self.team1,
            self.team2,
            self.team1_speakers,
            self.team2_speakers,
            {1: 63, 2: 60, 3: 57, 4: 45},
            {1: 57, 2: 54, 3: 51, 4: 48},
            276,
            258,
        )

        refresh_forfeit_ballots(self.tournament)

        refreshed_winner = TeamScore.objects.get(ballot_submission=ballotsub, debate_team=aff_dt)
        refreshed_loser = TeamScore.objects.get(ballot_submission=ballotsub, debate_team=neg_dt)
        refreshed_pos1 = SpeakerScore.objects.get(ballot_submission=ballotsub, debate_team=aff_dt, position=1)

        self.assertEqual(271.5, refreshed_winner.score)
        self.assertEqual(0, refreshed_loser.score)
        self.assertEqual(61.5, refreshed_pos1.score)
        self.assertEqual(0, SpeakerScore.objects.get(ballot_submission=ballotsub, debate_team=neg_dt, position=1).score)

        standings_generator = SpeakerStandingsGenerator(('average', 'total'), ())
        with suppress_logs('standings.metrics', logging.INFO):
            standings = standings_generator.generate(
                Speaker.objects.filter(team__tournament=self.tournament),
                tournament=self.tournament,
                round=self.tournament.round_set.order_by('seq').last(),
            )

        winner_standing = standings.get_standing(self.team1_speakers[0])
        loser_standing = standings.get_standing(self.team3_speakers[0])
        self.assertAlmostEqual(20.5, winner_standing.metrics['average'])
        self.assertAlmostEqual(184.5, winner_standing.metrics['total'])
        self.assertAlmostEqual(0, loser_standing.metrics['average'])
        self.assertAlmostEqual(0, loser_standing.metrics['total'])

    def test_bye_round_results_cell_shows_bye_score(self):
        debate, bye_dt = self._add_bye_debate(1, self.team1)

        refresh_bye_ballots(self.tournament)

        ballotsub = debate.ballotsubmission_set.get(confirmed=True)
        teamscore = TeamScore.objects.get(ballot_submission=ballotsub, debate_team=bye_dt)
        table = TabbycatTableBuilder(tournament=self.tournament, admin=True)

        cell = table._result_cell(teamscore, compress=True, show_score=True, show_ballots=True)

        self.assertEqual('Bye', cell['text'])
        self.assertIn('subtext', cell)
        self.assertNotEqual(table.BLANK_TEXT, cell['text'])

    def test_bye_averages_ignore_forfeit_awards(self):
        self._add_real_debate(
            1,
            self.team1,
            self.team2,
            self.team1_speakers,
            self.team2_speakers,
            {1: 60, 2: 57, 3: 54, 4: 48},
            {1: 54, 2: 51, 3: 48, 4: 45},
            267,
            246,
        )
        self._add_forfeit_debate(2, self.team1, self.team3, DebateSide.NEG)
        self._add_real_debate(
            3,
            self.team1,
            self.team3,
            self.team1_speakers,
            self.team3_speakers,
            {1: 66, 2: 63, 3: 60, 4: 51},
            {1: 57, 2: 54, 3: 51, 4: 48},
            282,
            258,
        )
        bye_debate, bye_dt = self._add_bye_debate(4, self.team1)

        refresh_forfeit_ballots(self.tournament)
        refresh_bye_ballots(self.tournament)

        ballotsub = bye_debate.ballotsubmission_set.get(confirmed=True)
        bye_teamscore = TeamScore.objects.get(ballot_submission=ballotsub, debate_team=bye_dt)
        bye_pos1 = SpeakerScore.objects.get(ballot_submission=ballotsub, debate_team=bye_dt, position=1)

        self.assertEqual(274.5, bye_teamscore.score)
        self.assertEqual(63, bye_pos1.score)
