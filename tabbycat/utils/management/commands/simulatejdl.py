import logging
import random
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from adjallocation.allocators.hungarian import VotingHungarianAllocator
from availability.utils import activate_all
from draw.manager import DrawManager
from draw.side_allocations import generate_opposite_allocations, generate_random_allocations
from options.presets import JDLFirstCategoryPreferences, JDLFormatPreferences
from participants.models import Adjudicator, Institution, Speaker, Team
from results.dbutils import add_results_to_round
from results.models import BallotSubmission, SpeakerScore, TeamScore
from standings.speakers import SpeakerStandingsGenerator
from standings.teams import TeamStandingsGenerator
from tournaments.models import Round, Tournament
from utils.management.base import _set_log_level
from venues.allocator import allocate_venues
from venues.models import Venue


User = get_user_model()


class Command(BaseCommand):
    help = (
        "Runs an end-to-end smoke simulation for JDL 1. category and JDL 2. "
        "category tournaments. By default all database writes are rolled back."
    )

    def add_arguments(self, parser):
        parser.add_argument("--rounds", type=int, default=3, help="Number of preliminary rounds to simulate.")
        parser.add_argument(
            "--first-category-speakers",
            type=int,
            default=13,
            help="Number of one-speaker JDL 1. category teams to create.",
        )
        parser.add_argument(
            "--second-category-speakers",
            type=int,
            default=20,
            help="Number of JDL 2. category speakers to create. Must be even.",
        )
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Keep the generated tournaments instead of rolling back all writes.",
        )
        parser.add_argument("--seed", type=int, default=20260602, help="Random seed for repeatable simulations.")

    def handle(self, *args, **options):
        if options["rounds"] < 1:
            raise CommandError("--rounds must be at least 1.")
        if options["first_category_speakers"] < 1:
            raise CommandError("--first-category-speakers must be at least 1.")
        if options["second_category_speakers"] % 2:
            raise CommandError("--second-category-speakers must be even for a 2 vs 2 format.")

        if options["verbosity"] < 2:
            _set_log_level(logging.WARNING)
        random.seed(options["seed"])

        if options["keep"]:
            summaries = self._run_suite(options)
            self._write_summary(summaries, kept=True)
            return

        with transaction.atomic():
            summaries = self._run_suite(options)
            self._write_summary(summaries, kept=False)
            transaction.set_rollback(True)

    def _run_suite(self, options):
        suffix = uuid4().hex[:8]
        user = User.objects.create_user(f"jdl-smoke-{suffix}", "", "jdl-smoke")

        first_summary = self._simulate_tournament(
            slug=f"jdl1-smoke-{suffix}",
            name="JDL 1 Smoke",
            preset=JDLFirstCategoryPreferences,
            team_count=options["first_category_speakers"],
            speakers_per_team=1,
            adjudicator_count=options["first_category_speakers"],
            venue_count=options["first_category_speakers"],
            round_count=options["rounds"],
            user=user,
            institution_code=f"J1{suffix[:6]}",
        )
        second_team_count = options["second_category_speakers"] // 2
        second_summary = self._simulate_tournament(
            slug=f"jdl2-smoke-{suffix}",
            name="JDL 2 Smoke",
            preset=JDLFormatPreferences,
            team_count=second_team_count,
            speakers_per_team=2,
            adjudicator_count=max(1, second_team_count // 2),
            venue_count=max(1, second_team_count // 2),
            round_count=options["rounds"],
            user=user,
            institution_code=f"J2{suffix[:6]}",
        )
        return [first_summary, second_summary]

    def _simulate_tournament(
        self,
        *,
        slug,
        name,
        preset,
        team_count,
        speakers_per_team,
        adjudicator_count,
        venue_count,
        round_count,
        user,
        institution_code,
    ):
        tournament = Tournament.objects.create(slug=slug, name=name, short_name=name)
        preset.save(tournament)
        preset.configure_feedback_questions(tournament)
        tournament._prefs.clear()

        institution = Institution.objects.create(code=institution_code, name=f"{name} Institution {institution_code}")
        self._create_teams(tournament, institution, team_count, speakers_per_team, slug)
        self._create_adjudicators(tournament, institution, adjudicator_count, slug)
        self._create_venues(tournament, venue_count)

        rounds = [
            Round.objects.create(
                tournament=tournament,
                seq=seq,
                name=f"Round {seq}",
                abbreviation=f"R{seq}",
                draw_type=Round.DrawType.RANDOM if seq == 1 else Round.DrawType.POWERPAIRED,
            )
            for seq in range(1, round_count + 1)
        ]

        round_summaries = []
        previous_round = None
        for round in rounds:
            round_summaries.append(self._simulate_round(round, previous_round, user, team_count))
            previous_round = round

        final_round = rounds[-1]
        team_standings_count = self._check_team_standings(tournament, final_round)
        speaker_standings_count = self._check_speaker_standings(tournament, final_round)

        return {
            "name": name,
            "slug": slug,
            "teams": team_count,
            "speakers": team_count * speakers_per_team,
            "rounds": round_summaries,
            "team_standings": team_standings_count,
            "speaker_standings": speaker_standings_count,
        }

    def _create_teams(self, tournament, institution, team_count, speakers_per_team, slug):
        for team_index in range(1, team_count + 1):
            team = Team.objects.create(
                tournament=tournament,
                institution=institution,
                reference=f"Team {team_index:02d}",
                short_reference=f"T{team_index:02d}",
                use_institution_prefix=False,
            )
            for speaker_index in range(1, speakers_per_team + 1):
                Speaker.objects.create(
                    team=team,
                    name=f"{team.reference} Speaker {speaker_index}",
                    url_key=self._url_key(slug, "s", team_index, speaker_index),
                )

    def _create_adjudicators(self, tournament, institution, adjudicator_count, slug):
        for index in range(1, adjudicator_count + 1):
            Adjudicator.objects.create(
                tournament=tournament,
                institution=institution,
                name=f"Judge {index:02d}",
                base_score=5,
                url_key=self._url_key(slug, "a", index),
            )

    def _create_venues(self, tournament, venue_count):
        for index in range(1, venue_count + 1):
            Venue.objects.create(tournament=tournament, name=f"Room {index:02d}", priority=100 - index)

    def _simulate_round(self, round, previous_round, user, team_count):
        activate_all(round)

        if previous_round is None:
            generate_random_allocations(round)
        else:
            generate_opposite_allocations(round, previous_round)

        DrawManager(round).create()
        round.draw_status = Round.Status.CONFIRMED
        round.save()

        self._allocate_adjudicators(round)
        allocate_venues(round)

        add_results_to_round(
            round,
            submitter_type=BallotSubmission.Submitter.TABROOM,
            user=user,
            confirmed=True,
        )

        round.completed = True
        round.save()

        return self._check_round(round, team_count)

    def _allocate_adjudicators(self, round):
        debates = round.debate_set.all()
        adjudicators = round.active_adjudicators.all()
        allocator = VotingHungarianAllocator(debates, adjudicators, round)
        allocation, _ = allocator.allocate()
        for alloc in allocation:
            alloc.save()

    def _check_round(self, round, team_count):
        teams_in_debate = round.tournament.pref("teams_in_debate")
        expected_debates = team_count if teams_in_debate == 1 else team_count // teams_in_debate
        expected_team_scores = expected_debates * teams_in_debate
        expected_speaker_scores = expected_team_scores * len(round.tournament.positions)

        debate_count = round.debate_set.count()
        if debate_count != expected_debates:
            raise CommandError(f"{round} generated {debate_count} debates, expected {expected_debates}.")
        if round.num_debates_without_chair:
            raise CommandError(f"{round} has debates without exactly one chair.")
        if round.num_debates_without_venue:
            raise CommandError(f"{round} has debates without rooms.")
        if round.num_debates_with_sides_unconfirmed:
            raise CommandError(f"{round} has debates with unconfirmed sides.")

        confirmed_ballots = BallotSubmission.objects.filter(debate__round=round, confirmed=True).count()
        team_scores = TeamScore.objects.filter(
            ballot_submission__debate__round=round,
            ballot_submission__confirmed=True,
        ).count()
        speaker_scores = SpeakerScore.objects.filter(
            ballot_submission__debate__round=round,
            ballot_submission__confirmed=True,
        ).count()

        if confirmed_ballots != expected_debates:
            raise CommandError(f"{round} has {confirmed_ballots} confirmed ballots, expected {expected_debates}.")
        if team_scores != expected_team_scores:
            raise CommandError(f"{round} has {team_scores} team scores, expected {expected_team_scores}.")
        if speaker_scores != expected_speaker_scores:
            raise CommandError(f"{round} has {speaker_scores} speaker scores, expected {expected_speaker_scores}.")

        return {
            "seq": round.seq,
            "debates": debate_count,
            "ballots": confirmed_ballots,
            "team_scores": team_scores,
            "speaker_scores": speaker_scores,
        }

    def _check_team_standings(self, tournament, round):
        standings = TeamStandingsGenerator(
            tournament.pref("team_standings_precedence"),
            ("rank",),
            tournament.pref("team_standings_extra_metrics"),
        ).generate(tournament.team_set.all(), round=round)
        count = len(list(standings))
        if count != tournament.team_set.count():
            raise CommandError(f"{tournament} team standings returned {count} rows.")
        return count

    def _check_speaker_standings(self, tournament, round):
        speakers = Speaker.objects.filter(team__tournament=tournament)
        standings = SpeakerStandingsGenerator(
            tournament.pref("speaker_standings_precedence"),
            ("rank",),
            tournament.pref("speaker_standings_extra_metrics"),
        ).generate(speakers, round=round)
        count = len(list(standings))
        if count != speakers.count():
            raise CommandError(f"{tournament} speaker standings returned {count} rows.")
        return count

    def _write_summary(self, summaries, *, kept):
        self.stdout.write(self.style.SUCCESS("JDL smoke simulation passed."))
        for summary in summaries:
            self.stdout.write(
                f"- {summary['name']} ({summary['speakers']} speakers, {summary['teams']} teams, "
                f"{len(summary['rounds'])} rounds)"
            )
            for round_summary in summary["rounds"]:
                self.stdout.write(
                    "  R{seq}: {debates} debates, {ballots} confirmed ballots, "
                    "{team_scores} team scores, {speaker_scores} speaker scores".format(**round_summary)
                )
            self.stdout.write(
                f"  standings: {summary['team_standings']} team rows, "
                f"{summary['speaker_standings']} speaker rows"
            )
            if kept:
                self.stdout.write(f"  kept tournament slug: {summary['slug']}")

        if not kept:
            self.stdout.write("All generated data was rolled back.")

    def _url_key(self, slug, prefix, *numbers):
        compact_slug = slug.replace("-", "")[:8]
        compact_numbers = "".join(f"{number:02d}" for number in numbers)
        return f"{compact_slug}{prefix}{compact_numbers}"[:24]
