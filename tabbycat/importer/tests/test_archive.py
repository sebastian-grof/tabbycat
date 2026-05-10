from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from adjallocation.models import DebateAdjudicator
from draw.models import Debate, DebateTeam
from draw.types import DebateSide
from importer.archive import Exporter, Importer
from importer.forms import ArchiveImportForm
from participants.models import Adjudicator, Institution, Speaker, Team
from results.models import (BallotSubmission, CrossExamination, CrossExaminationScore, ScoreCriterion,
    SpeakerScore, TeamScore)
from results.result import ConsensusDebateResultWithScores, DebateResultByAdjudicatorWithScores
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
        for seq, name in enumerate(("Strategy", "Organisation", "Analysis", "Evidence", "Presentation"), start=1):
            ScoreCriterion.objects.create(
                tournament=self.tournament, seq=seq, name=name, speech_type=ScoreCriterion.SpeechType.SUBSTANTIVE,
                weight=1, min_score=2, max_score=6, step=0.5,
            )
        for seq, name in enumerate(("Reply strategy", "Reply organisation", "Reply analysis", "Reply presentation"), start=6):
            ScoreCriterion.objects.create(
                tournament=self.tournament, seq=seq, name=name, speech_type=ScoreCriterion.SpeechType.REPLY,
                weight=1, min_score=2, max_score=6, step=0.5,
            )
        CrossExamination.objects.create(
            tournament=self.tournament, seq=1, name="Cross", weight=1, min_score=2, max_score=6, step=0.5,
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
        reply_speech = aff_side.findall("speech")[-1]

        expected_criteria = result.criteria_for_position(1)
        self.assertEqual(first_speech.get('reply'), 'false')
        self.assertEqual(reply_speech.get('reply'), 'true')
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
        root.set('short', 'arch-import-criteria')

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

    def test_import_accepts_legacy_uppercase_reply_attributes(self):
        ballotsub = BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        result = ConsensusDebateResultWithScores(
            ballotsub,
            criteria=list(self.tournament.scorecriterion_set.order_by('seq')),
            crosses=[],
            using_cross_examinations=False,
        )

        for side, speakers in ((DebateSide.AFF, self.aff_speakers), (DebateSide.NEG, self.neg_speakers)):
            for position in self.tournament.positions:
                speaker = speakers[0] if position == self.tournament.reply_position else speakers[position - 1]
                result.set_speaker(side, position, speaker)

        for position in self.tournament.positions:
            for criterion in result.criteria_for_position(position):
                result.set_criterion_score(DebateSide.AFF, position, criterion, 4.0)
                result.set_criterion_score(DebateSide.NEG, position, criterion, 3.0)

        result.save()

        root = Exporter(self.tournament).create_all()
        for speech in root.findall("round/debate/side/speech"):
            speech.set('reply', speech.get('reply').title())
        root.set('short', 'arch-import-uppercase')

        importer = Importer(root)
        importer.import_tournament()

        imported_tournament = importer.tournament
        imported_debate = imported_tournament.round_set.get(seq=1).debate_set.get()
        imported_result = imported_debate.confirmed_ballot.result

        self.assertEqual(imported_tournament.pref('substantive_speakers'), 3)
        self.assertTrue(imported_tournament.pref('reply_scores_enabled'))
        self.assertFalse(imported_tournament.pref('cross_examinations_enabled'))
        self.assertEqual(imported_tournament.positions, [1, 2, 3, 4])
        self.assertAlmostEqual(imported_result.get_score(DebateSide.AFF, 1), 20.0)
        self.assertAlmostEqual(imported_result.get_score(DebateSide.NEG, 1), 15.0)

    def test_import_legacy_per_adjudicator_archive_uses_weighted_scores(self):
        self.tournament.preferences['debate_rules__ballots_per_debate_prelim'] = 'per-adj'
        self.tournament.preferences['debate_rules__adjudicator_weighting'] = 'weighted-to-three'
        for key in ('ballots_per_debate_prelim', 'adjudicator_weighting'):
            self.tournament._prefs.pop(key, None)

        panel = Adjudicator.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            name="Panel",
            base_score=5,
        )
        DebateAdjudicator.objects.create(
            debate=self.debate,
            adjudicator=panel,
            type=DebateAdjudicator.TYPE_PANEL,
        )

        ballotsub = BallotSubmission.objects.create(debate=self.debate, confirmed=True)
        result = DebateResultByAdjudicatorWithScores(
            ballotsub,
            criteria=list(self.tournament.scorecriterion_set.order_by('seq')),
            crosses=[],
            using_cross_examinations=False,
        )

        for side, speakers in ((DebateSide.AFF, self.aff_speakers), (DebateSide.NEG, self.neg_speakers)):
            for position in self.tournament.positions:
                speaker = speakers[0] if position == self.tournament.reply_position else speakers[position - 1]
                result.set_speaker(side, position, speaker)

        for adjudicator, aff_score, neg_score in (
            (self.adjudicator, 20.0, 18.0),
            (panel, 19.0, 17.0),
        ):
            result.add_winner(adjudicator, DebateSide.AFF)
            for position in self.tournament.positions:
                criteria = result.criteria_for_position(position)
                for criterion in criteria:
                    result.set_criterion_score(adjudicator, DebateSide.AFF, position, criterion, aff_score / len(criteria))
                    result.set_criterion_score(adjudicator, DebateSide.NEG, position, criterion, neg_score / len(criteria))

        result.save()
        expected_aff_score = TeamScore.objects.get(
            ballot_submission=ballotsub,
            debate_team__side=DebateSide.AFF,
        ).score

        root = Exporter(self.tournament).create_all()
        self.assertEqual(root.get('adjudicator-weighting'), 'weighted-to-three')

        # Simulate an archive produced before the weighting preference and
        # aggregate team score were exported explicitly.
        del root.attrib['adjudicator-weighting']
        for ballot in root.findall("round/debate/side/ballot"):
            ballot.attrib.pop('score', None)
            ballot.attrib.pop('votes-given', None)
            ballot.attrib.pop('votes-possible', None)
        root.set('short', 'arch-import-weighted')

        importer = Importer(root, adjudicator_weighting='weighted-to-three')
        importer.import_tournament()

        imported_tournament = importer.tournament
        imported_ballot = imported_tournament.round_set.get(seq=1).debate_set.get().confirmed_ballot
        imported_aff_score = TeamScore.objects.get(
            ballot_submission=imported_ballot,
            debate_team__side=DebateSide.AFF,
        )

        self.assertEqual(imported_tournament.pref('adjudicator_weighting'), 'weighted-to-three')
        self.assertEqual(imported_aff_score.votes_possible, 3)
        self.assertAlmostEqual(imported_aff_score.score, expected_aff_score)
        first_adjudicator_speech_total = sum(
            float(speech.find('ballot').text)
            for speech in root.find("round/debate/side").findall('speech')
        )
        self.assertNotEqual(imported_aff_score.score, first_adjudicator_speech_total)

    def test_export_handles_bye_ballots_with_speaker_scores(self):
        bye_team = Team.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            reference="Bye",
            use_institution_prefix=False,
        )
        bye_speakers = [Speaker.objects.create(team=bye_team, name=f"Bye {i}") for i in range(1, 4)]
        bye_debate = Debate.objects.create(round=self.round)
        bye_dt = DebateTeam.objects.create(debate=bye_debate, team=bye_team, side=DebateSide.BYE)
        ballotsub = BallotSubmission.objects.create(debate=bye_debate, confirmed=True)

        TeamScore.objects.create(
            ballot_submission=ballotsub,
            debate_team=bye_dt,
            points=1,
            win=True,
            margin=None,
            score=243.0,
            votes_given=3,
            votes_possible=3,
            has_ghost=False,
        )

        for position in self.tournament.positions:
            speaker = bye_speakers[0] if position == self.tournament.reply_position else bye_speakers[position - 1]
            SpeakerScore.objects.create(
                ballot_submission=ballotsub,
                debate_team=bye_dt,
                speaker=speaker,
                position=position,
                score=81.0,
                rank=None,
                ghost=False,
            )

        root = Exporter(self.tournament).create_all()
        bye_debate_tag = root.find(f"./round/debate[@id='D{bye_debate.id}']")
        bye_sides = bye_debate_tag.findall("side")

        self.assertEqual(bye_debate_tag.get('bye'), 'true')
        self.assertEqual(len(bye_sides), 1)
        self.assertEqual(bye_sides[0].get('team'), f"T{bye_team.id}")
        self.assertEqual(bye_sides[0].find('ballot').get('rank'), '1')
        self.assertAlmostEqual(float(bye_sides[0].find('ballot').text), 243.0)
        self.assertEqual(len(bye_sides[0].findall('speech')), len(self.tournament.positions))
        self.assertAlmostEqual(float(bye_sides[0].find('speech/ballot').text), 81.0)

    def test_round_trip_import_preserves_bye_ballot_scores(self):
        bye_team = Team.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            reference="Bye",
            use_institution_prefix=False,
        )
        bye_speakers = [Speaker.objects.create(team=bye_team, name=f"Bye {i}") for i in range(1, 4)]
        bye_debate = Debate.objects.create(round=self.round)
        bye_dt = DebateTeam.objects.create(debate=bye_debate, team=bye_team, side=DebateSide.BYE)
        ballotsub = BallotSubmission.objects.create(debate=bye_debate, confirmed=True)

        TeamScore.objects.create(
            ballot_submission=ballotsub,
            debate_team=bye_dt,
            points=1,
            win=True,
            margin=None,
            score=255.0,
            votes_given=3,
            votes_possible=3,
            has_ghost=False,
        )

        for position in self.tournament.positions:
            speaker = bye_speakers[0] if position == self.tournament.reply_position else bye_speakers[position - 1]
            SpeakerScore.objects.create(
                ballot_submission=ballotsub,
                debate_team=bye_dt,
                speaker=speaker,
                position=position,
                score=81.0 if position != self.tournament.reply_position else 93.0,
                rank=None,
                ghost=False,
            )

        for cross in self.tournament.crossexamination_set.order_by('seq'):
            CrossExaminationScore.objects.create(
                ballot_submission=ballotsub,
                debate_team=bye_dt,
                cross_examination=cross,
                score=4.0,
            )

        root = Exporter(self.tournament).create_all()
        root.set('short', 'arch-import-bye')

        importer = Importer(root)
        importer.import_tournament()

        imported_tournament = importer.tournament
        imported_bye_debate = imported_tournament.round_set.get(seq=1).debate_set.get(debateteam__side=DebateSide.BYE)
        imported_ballot = imported_bye_debate.confirmed_ballot
        imported_result = imported_ballot.result
        imported_cross = imported_tournament.crossexamination_set.order_by('seq').first()

        self.assertTrue(imported_bye_debate.is_bye)
        self.assertEqual(imported_ballot.teamscore_set.get().votes_given, 3)
        self.assertAlmostEqual(imported_result.get_score(DebateSide.BYE, 1), 81.0)
        self.assertAlmostEqual(imported_result.get_score(DebateSide.BYE, imported_tournament.reply_position), 93.0)
        self.assertAlmostEqual(imported_result.get_cross_score(DebateSide.BYE, imported_cross), 4.0)

    def test_export_includes_forfeit_team_scores(self):
        ballotsub = BallotSubmission.objects.create(debate=self.debate, confirmed=True, forfeit=True)
        aff_dt = self.debate.get_dt(DebateSide.AFF)
        neg_dt = self.debate.get_dt(DebateSide.NEG)

        TeamScore.objects.create(
            ballot_submission=ballotsub,
            debate_team=aff_dt,
            points=1,
            win=True,
            margin=None,
            score=243.5,
            votes_given=3,
            votes_possible=3,
            has_ghost=False,
        )
        TeamScore.objects.create(
            ballot_submission=ballotsub,
            debate_team=neg_dt,
            points=0,
            win=False,
            margin=None,
            score=0.0,
            votes_given=0,
            votes_possible=3,
            has_ghost=False,
        )

        root = Exporter(self.tournament).create_all()
        debate_tag = root.find(f"./round/debate[@id='D{self.debate.id}']")
        aff_ballot = root.find(f"./round/debate/side[@team='T{self.aff_team.id}']/ballot")
        neg_ballot = root.find(f"./round/debate/side[@team='T{self.neg_team.id}']/ballot")

        self.assertEqual(debate_tag.get('forfeit'), 'true')
        self.assertEqual(aff_ballot.text, 'True')
        self.assertEqual(aff_ballot.get('score'), '243.5')
        self.assertEqual(aff_ballot.get('votes-given'), '3')
        self.assertEqual(neg_ballot.text, 'False')
        self.assertEqual(float(neg_ballot.get('score')), 0.0)
        self.assertEqual(neg_ballot.get('points'), '0')

    def test_round_trip_import_preserves_forfeit_team_scores(self):
        ballotsub = BallotSubmission.objects.create(debate=self.debate, confirmed=True, forfeit=True)
        aff_dt = self.debate.get_dt(DebateSide.AFF)
        neg_dt = self.debate.get_dt(DebateSide.NEG)

        TeamScore.objects.create(
            ballot_submission=ballotsub,
            debate_team=aff_dt,
            points=1,
            win=True,
            margin=None,
            score=251.0,
            votes_given=3,
            votes_possible=3,
            has_ghost=False,
        )
        TeamScore.objects.create(
            ballot_submission=ballotsub,
            debate_team=neg_dt,
            points=0,
            win=False,
            margin=None,
            score=0.0,
            votes_given=0,
            votes_possible=3,
            has_ghost=False,
        )

        root = Exporter(self.tournament).create_all()
        root.set('short', 'arch-import-forfeit')

        importer = Importer(root)
        importer.import_tournament()

        imported_tournament = importer.tournament
        imported_debate = imported_tournament.round_set.get(seq=1).debate_set.get()
        imported_ballot = imported_debate.confirmed_ballot
        imported_aff_dt = imported_debate.get_dt(DebateSide.AFF)
        imported_neg_dt = imported_debate.get_dt(DebateSide.NEG)
        imported_aff_ts = imported_ballot.teamscore_set.get(debate_team=imported_aff_dt)
        imported_neg_ts = imported_ballot.teamscore_set.get(debate_team=imported_neg_dt)

        self.assertTrue(imported_ballot.forfeit)
        self.assertAlmostEqual(imported_aff_ts.score, 251.0)
        self.assertEqual(imported_aff_ts.votes_given, 3)
        self.assertEqual(imported_aff_ts.votes_possible, 3)
        self.assertAlmostEqual(imported_neg_ts.score, 0.0)
        self.assertEqual(imported_neg_ts.points, 0)
        self.assertEqual(imported_neg_ts.votes_given, 0)


class TestArchiveImportForm(TestCase):

    def test_accepts_uploaded_xml_file(self):
        upload = SimpleUploadedFile(
            "archive.xml",
            b"<tournament name='Archive Test' short='archive-test'></tournament>",
            content_type="text/xml",
        )

        form = ArchiveImportForm(data={'xml': ''}, files={'xml_file': upload})

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['xml_root'].tag, 'tournament')
