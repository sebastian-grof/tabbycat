import zipfile
from io import BytesIO
from xml.etree import ElementTree as ET

from django.test import TestCase

from adjallocation.models import DebateAdjudicator
from draw.models import Debate, DebateTeam
from draw.types import DebateSide
from motions.models import Motion, RoundMotion
from options.presets import JDLFirstCategoryPreferences, SDLFormatPreferences
from participants.models import Adjudicator, Institution, Speaker, Team
from results.jdl_ballot_export import build_jdl_first_category_ballot_xlsx
from results.models import (
    BallotSubmission,
    BallotTextFeedback,
    ScoreCriterion,
    SpeakerCriterionScoreByAdj,
    SpeakerScore,
    SpeakerScoreByAdj,
)
from tournaments.models import Round, Tournament
from venues.models import Venue


MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


class JDLFirstCategoryBallotExportTests(TestCase):

    def setUp(self):
        self.tournament = Tournament.objects.create(slug="jdl1", name="JDL Test")
        JDLFirstCategoryPreferences.save(self.tournament)
        self.round = Round.objects.create(tournament=self.tournament, seq=1, name="Round 1", abbreviation="R1")
        self.venue = Venue.objects.create(name="Room", priority=1)
        self.debate = Debate.objects.create(round=self.round, venue=self.venue)
        self.motion = Motion.objects.create(
            tournament=self.tournament,
            text="This House would test XLSX exports",
            reference="M1",
        )
        RoundMotion.objects.create(round=self.round, motion=self.motion, seq=1)

        self.institution = Institution.objects.create(code="SDA", name="SDA")
        self.team = Team.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            reference="Solo Team",
            use_institution_prefix=False,
        )
        self.speaker = Speaker.objects.create(team=self.team, name="Jana Rečníčka")
        self.debate_team = DebateTeam.objects.create(debate=self.debate, team=self.team, side=DebateSide.AFF)
        self.ballot = BallotSubmission.objects.create(
            debate=self.debate,
            motion=self.motion,
            submitter_type=BallotSubmission.Submitter.TABROOM,
            confirmed=True,
        )
        SpeakerScore.objects.create(
            ballot_submission=self.ballot,
            debate_team=self.debate_team,
            speaker=self.speaker,
            position=1,
            score=20,
        )
        BallotTextFeedback.objects.create(ballot_submission=self.ballot, text="Dobré poznámky.")

        self.criteria = [
            ScoreCriterion.objects.create(
                tournament=self.tournament,
                seq=index,
                name=name,
                weight=1,
                min_score=2,
                max_score=6,
                step=1,
                speech_type=ScoreCriterion.SpeechType.SUBSTANTIVE,
            )
            for index, name in enumerate(
                ["Stratégia", "Organizácia", "Analýza", "Dôkazy", "Prezentácia"],
                start=1,
            )
        ]

    def _add_adjudicator(self, name, type=DebateAdjudicator.TYPE_PANEL):
        adj = Adjudicator.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            name=name,
            base_score=5,
            url_key=name.lower().replace(" ", "-"),
        )
        debate_adj = DebateAdjudicator.objects.create(debate=self.debate, adjudicator=adj, type=type)
        speaker_score = SpeakerScoreByAdj.objects.create(
            ballot_submission=self.ballot,
            debate_adjudicator=debate_adj,
            debate_team=self.debate_team,
            position=1,
            score=20,
        )
        for index, criterion in enumerate(self.criteria, start=1):
            SpeakerCriterionScoreByAdj.objects.create(
                speaker_score_by_adj=speaker_score,
                criterion=criterion,
                score=index,
            )
        return debate_adj

    def _cells(self):
        contents = build_jdl_first_category_ballot_xlsx(self.ballot)
        with zipfile.ZipFile(BytesIO(contents)) as zf:
            sheet = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))

        values = {}
        for cell in sheet.findall(f".//{MAIN_NS}c"):
            ref = cell.attrib.get("r")
            inline = cell.find(f"{MAIN_NS}is/{MAIN_NS}t")
            if inline is not None:
                values[ref] = inline.text or ""
                continue
            value = cell.find(f"{MAIN_NS}v")
            if value is not None:
                values[ref] = value.text
        return values

    def test_one_adjudicator_is_repeated_across_three_slots(self):
        self._add_adjudicator("Anna Chair", DebateAdjudicator.TYPE_CHAIR)

        cells = self._cells()

        self.assertEqual(cells["D3"], "JDL Test")
        self.assertEqual(cells["D5"], "This House would test XLSX exports")
        self.assertEqual(cells["Y3"], "Affirmative")
        self.assertEqual(cells["L8"], "Jana Rečníčka")
        self.assertEqual([cells["L9"], cells["M9"], cells["N9"]], ["chair", "chair", "chair"])
        self.assertEqual([cells["L10"], cells["M10"], cells["N10"]], ["1", "1", "1"])
        self.assertEqual(cells["A19"], "Dobré poznámky.")
        self.assertEqual(cells["I36"], "chair")

    def test_two_adjudicators_repeat_chair_twice(self):
        self._add_adjudicator("Anna Chair", DebateAdjudicator.TYPE_CHAIR)
        self._add_adjudicator("Peter Panel", DebateAdjudicator.TYPE_PANEL)

        cells = self._cells()

        self.assertEqual([cells["L9"], cells["M9"], cells["N9"]], ["chair", "chair", "panel"])
        self.assertEqual([cells["L10"], cells["M10"], cells["N10"]], ["1", "1", "1"])

    def test_three_adjudicators_each_get_one_slot(self):
        self._add_adjudicator("Anna Chair", DebateAdjudicator.TYPE_CHAIR)
        self._add_adjudicator("Peter Panel", DebateAdjudicator.TYPE_PANEL)
        self._add_adjudicator("Eva Panelova", DebateAdjudicator.TYPE_PANEL)

        cells = self._cells()

        self.assertEqual([cells["L9"], cells["M9"], cells["N9"]], ["chair", "panel", "panelova"])

    def test_export_is_off_for_sdl_preset(self):
        tournament = Tournament.objects.create(slug="sdl", name="SDL")
        SDLFormatPreferences.save(tournament)

        self.assertEqual(tournament.pref('ballot_export_format'), 'off')
