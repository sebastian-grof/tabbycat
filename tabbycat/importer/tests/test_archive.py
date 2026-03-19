from django.test import TestCase

from adjallocation.models import DebateAdjudicator
from draw.models import Debate, DebateTeam
from draw.types import DebateSide
from importer.archive import Exporter, Importer
from participants.models import Adjudicator, Institution, Speaker, Team
from results.models import BallotSubmission
from results.result import ConsensusDebateResultWithScores
from tournaments.models import Round, Tournament


class TestArchiveExporter(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug="archive-test", name="Archive Test")
        self.tournament.preferences['debate_rules__cross_examinations_enabled'] = True
        self.tournament.preferences['debate_rules__ballots_per_debate_prelim'] = 'per-debate'
        for key in ('cross_examinations_enabled', 'ballots_per_debate_prelim'):
            self.tournament._prefs.pop(key, None)

        self.institution = Institution.objects.create(code="I1", name="Institution 1")
        self.aff_team = Team.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            reference="Aff",
            use_institution_prefix=False,
        )
        self.neg_team = Team.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            reference="Neg",
            use_institution_prefix=False,
        )
        self.aff_speakers = [Speaker.objects.create(team=self.aff_team, name=f"Aff {i}") for i in range(1, 4)]
        self.neg_speakers = [Speaker.objects.create(team=self.neg_team, name=f"Neg {i}") for i in range(1, 4)]
        self.adjudicator = Adjudicator.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            name="Chair",
            base_score=5,
        )

        self.round = Round.objects.create(tournament=self.tournament, seq=1, abbreviation="R1")
        self.debate = Debate.objects.create(round=self.round)
        DebateTeam.objects.create(debate=self.debate, team=self.aff_team, side=DebateSide.AFF)
        DebateTeam.objects.create(debate=self.debate, team=self.neg_team, side=DebateSide.NEG)
        DebateAdjudicator.objects.create(
            debate=self.debate,
            adjudicator=self.adjudicator,
            type=DebateAdjudicator.TYPE_CHAIR,
        )

    def test_export_includes_speech_criteria_and_cross_scores(self):
        ballotsub = BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        result = ConsensusDebateResultWithScores(
            ballotsub,
            criteria=list(self.tournament.scorecriterion_set.order_by('seq')),
            crosses=list(self.tournament.crossexamination_set.order_by('seq')),
            using_cross_examinations=True,
        )

        for side, speakers in ((DebateSide.AFF, self.aff_speakers), (DebateSide.NEG, self.neg_speakers)):
            for position in self.tournament.positions:
                speaker = speakers[0] if position == self.tournament.reply_position else speakers[position - 1]
                result.set_speaker(side, position, speaker)

        for position in self.tournament.positions:
            for criterion in result.criteria_for_position(position):
                aff_score = 4.0 if position != self.tournament.reply_position else 5.0
                neg_score = 3.0 if position != self.tournament.reply_position else 4.0
                result.set_criterion_score(DebateSide.AFF, position, criterion, aff_score)
                result.set_criterion_score(DebateSide.NEG, position, criterion, neg_score)

        for cross in result.crosses:
            result.set_cross_score(DebateSide.AFF, cross, 4.0)
            result.set_cross_score(DebateSide.NEG, cross, 3.0)

        result.save()

        root = Exporter(self.tournament).create_all()
        aff_side = root.find(f"./round/debate/side[@team='T{self.aff_team.id}']")
        first_speech = aff_side.find("speech")
        criteria = first_speech.findall("criterion")
        crosses = aff_side.findall("cross")

        expected_criteria = result.criteria_for_position(1)
        self.assertEqual(len(criteria), len(expected_criteria))
        self.assertEqual(criteria[0].get('name'), expected_criteria[0].name)
        self.assertAlmostEqual(float(criteria[0].find('ballot').text), 4.0)

        expected_crosses = list(self.tournament.crossexamination_set.order_by('seq'))
        self.assertEqual(len(crosses), len(expected_crosses))
        self.assertEqual(crosses[0].get('name'), expected_crosses[0].name)
        self.assertAlmostEqual(float(crosses[0].find('ballot').text), 4.0)

    def test_round_trip_import_preserves_criteria_and_cross_scores(self):
        ballotsub = BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        result = ConsensusDebateResultWithScores(
            ballotsub,
            criteria=list(self.tournament.scorecriterion_set.order_by('seq')),
            crosses=list(self.tournament.crossexamination_set.order_by('seq')),
            using_cross_examinations=True,
        )

        for side, speakers in ((DebateSide.AFF, self.aff_speakers), (DebateSide.NEG, self.neg_speakers)):
            for position in self.tournament.positions:
                speaker = speakers[0] if position == self.tournament.reply_position else speakers[position - 1]
                result.set_speaker(side, position, speaker)

        first_criterion = result.criteria_for_position(1)[0]
        first_cross = result.crosses[0]

        for position in self.tournament.positions:
            for criterion in result.criteria_for_position(position):
                result.set_criterion_score(DebateSide.AFF, position, criterion, 4.0)
                result.set_criterion_score(DebateSide.NEG, position, criterion, 3.0)

        for cross in result.crosses:
            result.set_cross_score(DebateSide.AFF, cross, 4.0)
            result.set_cross_score(DebateSide.NEG, cross, 3.0)

        result.save()

        root = Exporter(self.tournament).create_all()
        self.tournament.delete()

        importer = Importer(root)
        importer.import_tournament()

        imported_tournament = importer.tournament
        imported_debate = imported_tournament.round_set.get(seq=1).debate_set.get()
        imported_result = imported_debate.confirmed_ballot.result
        imported_first_criterion = imported_tournament.scorecriterion_set.get(seq=first_criterion.seq)
        imported_first_cross = imported_tournament.crossexamination_set.get(seq=first_cross.seq)

        self.assertEqual(imported_first_criterion.name, first_criterion.name)
        self.assertEqual(imported_first_cross.name, first_cross.name)
        self.assertAlmostEqual(
            imported_result.get_criterion_score(DebateSide.AFF, 1, imported_first_criterion),
            4.0,
        )
        self.assertAlmostEqual(
            imported_result.get_criterion_score(DebateSide.NEG, 1, imported_first_criterion),
            3.0,
        )
        self.assertAlmostEqual(
            imported_result.get_cross_score(DebateSide.AFF, imported_first_cross),
            4.0,
        )
        self.assertAlmostEqual(
            imported_result.get_cross_score(DebateSide.NEG, imported_first_cross),
            3.0,
        )
