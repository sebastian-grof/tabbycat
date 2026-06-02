from django.contrib.auth import get_user_model
from django.test import TestCase

from adjallocation.models import DebateAdjudicator
from draw.models import Debate, DebateTeam
from draw.types import DebateSide
from options.presets import JDLFirstCategoryPreferences
from participants.models import Adjudicator, Institution, Speaker, Team
from results.dbutils import add_result
from results.models import BallotSubmission, SpeakerScore, TeamScore
from tournaments.models import Round, Tournament
from venues.models import Venue


User = get_user_model()


class JDLSoloGenerateResultsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("jdl-generator")
        self.tournament = Tournament.objects.create(slug="jdl-generator", name="JDL Generator")
        JDLFirstCategoryPreferences.save(self.tournament)
        self.round = Round.objects.create(
            tournament=self.tournament,
            seq=1,
            name="Round 1",
            abbreviation="R1",
            draw_type=Round.DrawType.RANDOM,
        )
        self.venue = Venue.objects.create(tournament=self.tournament, name="Room A", priority=1)
        self.institution = Institution.objects.create(code="JDL", name="JDL")
        self.adjudicator = Adjudicator.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            name="Judge",
            base_score=5,
        )
        self.team = Team.objects.create(
            tournament=self.tournament,
            institution=self.institution,
            reference="Speaker Team",
            use_institution_prefix=False,
        )
        self.speaker = Speaker.objects.create(team=self.team, name="Speaker")
        self.debate = Debate.objects.create(round=self.round, venue=self.venue)
        DebateTeam.objects.create(debate=self.debate, team=self.team, side=DebateSide.AFF)
        DebateAdjudicator.objects.create(
            debate=self.debate,
            adjudicator=self.adjudicator,
            type=DebateAdjudicator.TYPE_CHAIR,
        )

    def test_random_result_generation_handles_solo_speech_debate(self):
        result = add_result(
            self.debate,
            submitter_type=BallotSubmission.Submitter.TABROOM,
            user=self.user,
            confirmed=True,
        )

        self.assertTrue(result.is_valid())
        self.assertEqual(1, BallotSubmission.objects.filter(debate=self.debate, confirmed=True).count())
        self.assertEqual(1, TeamScore.objects.filter(ballot_submission__debate=self.debate).count())
        self.assertEqual(1, SpeakerScore.objects.filter(ballot_submission__debate=self.debate).count())
