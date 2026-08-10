import unittest
from dataclasses import dataclass

from draw.types import DebateSide

from ..scoresheet import (HighPointWinsRequiredScoresheet, LowPointWinsAllowedScoresheet,
    PolyScoresheet, ResultOnlyScoresheet, TiedPointWinsAllowedScoresheet)


def on_all_testdata(test_fn):
    """Decorator. Tests should be written to take two arguments: self,
     testdata. 'scoresheet' is a Scoresheet object. 'testdata'
    is a value of BaseBaseScoresheet.testdata. This decorator then sets up
    the scoresheet and runs the test once for each test dataset in
    BaseBaseScoresheet.testdata."""
    def foo(self):
        for testdata in self.testdata.values():
            test_fn(self, testdata)
    return foo


@dataclass(frozen=True)
class Criterion:
    weight: float
    speech_type: str

    def applies_to_position(self, position, reply_position=None, using_replies=True):
        if self.speech_type == 'all':
            return True
        if not using_replies:
            return self.speech_type == 'substantive'
        return (self.speech_type == 'reply') == (position == reply_position)


class TestTwoTeamScoresheets(unittest.TestCase):

    sides = [DebateSide.AFF, DebateSide.NEG]

    testdata = dict()
    testdata[1] = {  # normal
        'positions': [1, 2, 3, 4],
        'scores': [[75.0, 76.0, 74.0, 38.0], [76.0, 73.0, 75.0, 37.5]],
        'declared_winner': DebateSide.AFF,
        'complete_scores': True,
        'complete_declared': True,
        'totals': [263, 261.5],
        'calculated_winner': DebateSide.AFF,
    }
    testdata[2] = {  # low-point win
        'positions': [1, 2, 3],
        'scores': [[73.0, 70.0, 40.0], [80.0, 78.0, 38.5]],
        'declared_winner': DebateSide.AFF,
        'complete_scores': True,
        'complete_declared': True,
        'totals': [183.0, 196.5],
        'calculated_winner': DebateSide.NEG,
    }
    testdata[3] = {  # tie-point win
        'positions': [1, 2, 3, 4],
        'scores': [[75.0, 76.0, 77.0, 38.5], [76.0, 78.0, 75.0, 37.5]],
        'declared_winner': DebateSide.NEG,
        'complete_scores': True,
        'complete_declared': True,
        'totals': [266.5, 266.5],
        'calculated_winner': None,
    }
    testdata[4] = {  # incomplete
        'positions': [1, 2, 3, 4],
        'scores': [[75.0, 76.0, 77.0, 38.5], [76.0, 78.0, None, 37.5]],
        'declared_winner': DebateSide.NEG,
        'complete_scores': False,
        'complete_declared': True,
        'totals': [266.5, None],
        'calculated_winner': None,
    }
    testdata[5] = {  # incomplete
        'positions': [1, 2, 3],
        'scores': [[73.0, 70.0, 40.0], [80.0, 78.0, 38.5]],
        'declared_winner': None,
        'complete_scores': True,
        'complete_declared': False,
        'totals': [183.0, 196.5],
        'calculated_winner': DebateSide.NEG,
    }

    def load_scores(self, scoresheet, testdata):
        for side, scores_for_side in zip(self.sides, testdata['scores']):
            for position, score in zip(testdata['positions'], scores_for_side):
                scoresheet.set_score(side, position, score)

    def assert_scores(self, scoresheet, testdata):
        for side, total in zip(self.sides, testdata['totals']):
            self.assertEqual(scoresheet.get_total(side), total)
        for side, scores_for_side in zip(self.sides, testdata['scores']):
            for position, score in zip(testdata['positions'], scores_for_side):
                self.assertEqual(scoresheet.get_score(side, position), score)

    @on_all_testdata
    def test_result_only(self, testdata):
        scoresheet = ResultOnlyScoresheet()
        scoresheet.add_declared_winner(testdata['declared_winner'])
        self.assertEqual(scoresheet.is_complete(), testdata['complete_declared'])
        if scoresheet.is_complete():
            self.assertEqual(next(iter(scoresheet.winners()), None), testdata['declared_winner'])
            self.assertEqual(len(scoresheet.winners()), 1)
        else:
            self.assertEqual(len(scoresheet.winners()), 0)

    @on_all_testdata
    def test_high_points_required(self, testdata):
        scoresheet = HighPointWinsRequiredScoresheet(testdata['positions'])
        self.load_scores(scoresheet, testdata)
        self.assertEqual(scoresheet.is_complete(), testdata['complete_scores'])
        if testdata['calculated_winner'] is None:
            self.assertEqual(len(scoresheet.winners()), 0)
        else:
            self.assertEqual(next(iter(scoresheet.winners()), None), testdata['calculated_winner'])
        self.assert_scores(scoresheet, testdata)
        self.assertEqual(scoresheet.is_valid(), testdata['calculated_winner'] is not None)

    @on_all_testdata
    def test_low_point_win(self, testdata):
        scoresheet = LowPointWinsAllowedScoresheet(testdata['positions'])
        scoresheet.add_declared_winner(testdata['declared_winner'])
        self.load_scores(scoresheet, testdata)
        self.assertEqual(scoresheet.is_complete(), testdata['complete_scores'] and testdata['complete_declared'])
        if scoresheet.is_complete():
            self.assertEqual(len(scoresheet.winners()), 1)
            self.assertEqual(next(iter(scoresheet.winners()), None), testdata['declared_winner'])
        else:
            self.assertEqual(len(scoresheet.winners()), 0)
        self.assert_scores(scoresheet, testdata)
        self.assertEqual(scoresheet.is_valid(), testdata['complete_scores'] and testdata['complete_declared'])

    @on_all_testdata
    def test_tie_point_win(self, testdata):
        scoresheet = TiedPointWinsAllowedScoresheet(testdata['positions'])
        scoresheet.add_declared_winner(testdata['declared_winner'])
        self.load_scores(scoresheet, testdata)
        self.assertEqual(scoresheet.is_complete(), testdata['complete_scores'] and testdata['complete_declared'])
        if scoresheet.is_complete() and (testdata['calculated_winner'] in [testdata['declared_winner'], None]):
            winner = testdata['declared_winner']
            self.assertEqual(next(iter(scoresheet.winners()), None), winner)
            self.assertEqual(len(scoresheet.winners()), 1)
        else:
            winner = None
            self.assertEqual(len(scoresheet.winners()), 0)
        self.assert_scores(scoresheet, testdata)
        self.assertEqual(scoresheet.is_valid(), winner is not None)

    def test_declared_winner_error(self):
        scoresheet = ResultOnlyScoresheet()
        self.assertRaises(AssertionError, scoresheet.set_declared_winners, set(['hello']))

    def test_criteria_can_apply_to_substantive_or_reply_speeches(self):
        substantive = Criterion(1, 'substantive')
        reply = Criterion(1, 'reply')
        scoresheet = HighPointWinsRequiredScoresheet(
            [1, 2, 3, 4],
            criteria=[substantive, reply],
            reply_position=4,
            using_replies=True,
        )

        scoresheet.set_criterion_score(DebateSide.AFF, 1, substantive, 80)
        scoresheet.set_criterion_score(DebateSide.AFF, 1, reply, 40)
        scoresheet.set_criterion_score(DebateSide.AFF, 4, substantive, 80)
        scoresheet.set_criterion_score(DebateSide.AFF, 4, reply, 40)

        self.assertEqual(scoresheet.get_score(DebateSide.AFF, 1), 80)
        self.assertEqual(scoresheet.get_score(DebateSide.AFF, 4), 40)


class TestPolyScoresheets(unittest.TestCase):

    sides = [DebateSide.OG, DebateSide.OO, DebateSide.CG, DebateSide.CO]
    positions = [1, 2]

    testdata = {}

    testdata[1] = {  # normal
        'scores': [[76, 69], [76, 70], [72, 85], [69, 85]],
        'complete': True,
        'ranks': [DebateSide.CG, DebateSide.CO, DebateSide.OO, DebateSide.OG],
        'totals': [145, 146, 157, 154],
    }
    testdata[1] = {  # normal
        'scores': [[75, 75], [75, 74], [75, 76], [76, 76]],
        'complete': True,
        'ranks': [DebateSide.CO, DebateSide.CG, DebateSide.OG, DebateSide.OO],
        'totals': [150, 149, 151, 152],
    }
    testdata[1] = {  # tie-point
        'scores': [[84, 81], [80, 69], [81, 68], [85, 68]],
        'complete': True,
        'ranks': [],
        'totals': [165, 149, 149, 153],
    }
    testdata[2] = { # incomplete
        'scores': [[84, None], [80, 69], [None, 68], [85, 68]],
        'complete': False,
        'ranks': [],
        'totals': [None, 149, None, 153],
    }

    def load_scores(self, scoresheet, testdata):
        for side, scores_for_side in zip(self.sides, testdata['scores']):
            for position, score in zip(self.positions, scores_for_side):
                scoresheet.set_score(side, position, score)

    @on_all_testdata
    def test_bp_scoresheet(self, testdata):
        scoresheet = PolyScoresheet(self.positions, self.sides)
        self.load_scores(scoresheet, testdata)
        self.assertEqual(scoresheet.is_complete(), testdata['complete'])
        self.assertEqual(scoresheet.ranked_sides(), testdata['ranks'])
        if testdata['ranks'] is not None:
            for side, rank in zip(self.sides, testdata['ranks']):
                self.assertEqual(scoresheet.rank(side), testdata['ranks'].index(side))
        else:
            for side in self.sides:
                self.assertEqual(scoresheet.rank(side), None)
        for side, total in zip(self.sides, testdata['totals']):
            self.assertEqual(scoresheet.get_total(side), total)
        for side, scores_for_side in zip(self.sides, testdata['scores']):
            for position, score in zip(self.positions, scores_for_side):
                self.assertEqual(scoresheet.get_score(side, position), score)
        self.assertEqual(scoresheet.is_valid(), len(testdata['ranks']) > 0)


class CriterionStub:
    def __init__(self, name, weight, speech_type):
        self.name = name
        self.weight = weight
        self.speech_type = speech_type

    def applies_to_position(self, position, reply_position, using_replies):
        # Mirrors ScoreCriterion.applies_to_position in results.models
        if self.speech_type == 'all':
            return True
        is_reply_position = bool(using_replies) and reply_position is not None and position == reply_position
        if self.speech_type == 'reply':
            return is_reply_position
        if self.speech_type == 'substantive':
            return not is_reply_position
        if self.speech_type == 'cross':
            return False
        return True


class TestSpeechTypeCriteria(unittest.TestCase):

    def test_reply_and_substantive_criteria_are_scoped_by_position(self):
        substantive = CriterionStub('substantive', 1, 'substantive')
        reply = CriterionStub('reply', 1, 'reply')
        scoresheet = HighPointWinsRequiredScoresheet(
            positions=[1, 2, 3, 4],
            criteria=[substantive, reply],
            reply_position=4,
            using_replies=True,
        )

        for side, substantive_score in ((DebateSide.AFF, 75), (DebateSide.NEG, 70)):
            for pos in [1, 2, 3]:
                scoresheet.set_criterion_score(side, pos, substantive, substantive_score)

        scoresheet.set_criterion_score(DebateSide.AFF, 4, reply, 38)
        scoresheet.set_criterion_score(DebateSide.NEG, 4, reply, 36)

        # Non-applicable criteria should be ignored.
        scoresheet.set_criterion_score(DebateSide.AFF, 4, substantive, 999)
        scoresheet.set_criterion_score(DebateSide.AFF, 1, reply, 999)

        self.assertEqual(scoresheet.get_score(DebateSide.AFF, 1), 75)
        self.assertEqual(scoresheet.get_score(DebateSide.AFF, 4), 38)
        self.assertEqual(scoresheet.get_total(DebateSide.AFF), 263)
        self.assertEqual(scoresheet.get_total(DebateSide.NEG), 246)

    def test_positions_without_criteria_use_direct_scores(self):
        reply = CriterionStub('reply', 1, 'reply')
        scoresheet = HighPointWinsRequiredScoresheet(
            positions=[1, 2, 3, 4],
            criteria=[reply],
            reply_position=4,
            using_replies=True,
        )

        for pos in [1, 2, 3]:
            scoresheet.set_score(DebateSide.AFF, pos, 75)
            scoresheet.set_score(DebateSide.NEG, pos, 74)

        scoresheet.set_criterion_score(DebateSide.AFF, 4, reply, 38)
        scoresheet.set_criterion_score(DebateSide.NEG, 4, reply, 37)

        # Direct scores on a criterion-backed position should be ignored.
        scoresheet.set_score(DebateSide.AFF, 4, 999)

        self.assertEqual(scoresheet.get_score(DebateSide.AFF, 1), 75)
        self.assertEqual(scoresheet.get_score(DebateSide.AFF, 4), 38)
        self.assertIsNone(scoresheet.get_criterion_score(DebateSide.AFF, 1, reply))
        self.assertEqual(scoresheet.get_total(DebateSide.AFF), 263)
        self.assertEqual(scoresheet.get_total(DebateSide.NEG), 259)
        self.assertTrue(scoresheet.is_complete())


class CrossStub:
    def __init__(self, weight=1, required=True):
        self.weight = weight
        self.required = required


class TestCrossExaminationToggle(unittest.TestCase):

    def test_crosses_do_not_auto_enable_from_cross_definitions_alone(self):
        cross = CrossStub()
        scoresheet = HighPointWinsRequiredScoresheet(
            positions=[1, 2, 3],
            crosses=[cross],
        )

        for side in (DebateSide.AFF, DebateSide.NEG):
            for pos in [1, 2, 3]:
                scoresheet.set_score(side, pos, 75)

        self.assertFalse(scoresheet.using_cross_examinations)
        self.assertTrue(scoresheet.is_complete())
        self.assertEqual(scoresheet.get_total(DebateSide.AFF), 225)

    def test_crosses_only_apply_when_explicitly_enabled(self):
        cross = CrossStub(weight=2)
        scoresheet = HighPointWinsRequiredScoresheet(
            positions=[1, 2, 3],
            crosses=[cross],
            using_cross_examinations=True,
        )

        for side in (DebateSide.AFF, DebateSide.NEG):
            for pos in [1, 2, 3]:
                scoresheet.set_score(side, pos, 75)

        scoresheet.set_cross_score(DebateSide.AFF, cross, 4)
        scoresheet.set_cross_score(DebateSide.NEG, cross, 3)

        self.assertTrue(scoresheet.using_cross_examinations)
        self.assertTrue(scoresheet.is_complete())
        self.assertEqual(scoresheet.get_total(DebateSide.AFF), 233)
        self.assertEqual(scoresheet.get_total(DebateSide.NEG), 231)
