import logging
import random
from collections import Counter
from typing import List, Tuple, TYPE_CHECKING

from django.utils.translation import gettext as _

from draw.generator.powerpair import BasePowerPairedDrawGenerator
from participants.utils import get_side_history
from results.bye_scores import refresh_bye_ballots
from standings.teams import TeamStandingsGenerator
from tournaments.models import Round

from .generator import BPEliminationResultPairing, DrawGenerator, DrawUserError, ResultPairing
from .generator.utils import ispow2
from .models import ByeTeamOverride, Debate, DebateTeam, TeamSideAllocation, get_effective_side_allocation_mode
from .side_allocation_pairings import apply_postallocated_sides
from .types import DebateSide

if TYPE_CHECKING:
    from participants.models import Team

    from .generator.pairing import BasePairing

logger = logging.getLogger(__name__)

OPTIONS_TO_CONFIG_MAPPING = {
    "avoid_institution"     : "draw_rules__avoid_same_institution",
    "avoid_history"         : "draw_rules__avoid_team_history",
    "history_penalty"       : "draw_rules__team_history_penalty",
    "institution_penalty"   : "draw_rules__team_institution_penalty",
    "pullup_debates_penalty": "draw_rules__pullup_debates_penalty",
    "side_penalty"          : "draw_rules__side_penalty",
    "pairing_penalty"       : "draw_rules__pairing_penalty",
    "side_allocations"      : "draw_rules__draw_side_allocations",
    "avoid_conflicts"       : "draw_rules__draw_avoid_conflicts",
    "odd_bracket"           : "draw_rules__draw_odd_bracket",
    "pairing_method"        : "draw_rules__draw_pairing_method",
    "pullup_restriction"    : "draw_rules__draw_pullup_restriction",
    "max_times_per_side"    : "draw_rules__max_times_per_side",
    "pullup"                : "draw_rules__bp_pullup_distribution",
    "position_cost"         : "draw_rules__bp_position_cost",
    "assignment_method"     : "draw_rules__bp_assignment_method",
    "renyi_order"           : "draw_rules__bp_renyi_order",
    "exponent"              : "draw_rules__bp_position_cost_exponent",
    "max_times_on_one_side" : "draw_rules__max_times_per_side",
    "pullup_penalty"        : "draw_rules__draw_pullup_penalty",
}


def DrawManager(round: Round, active_only: bool = True, draw_type: Round.DrawType | str | None = None):  # noqa: N802 (factory function)
    teams_in_debate = round.tournament.pref('teams_in_debate')
    draw_type = draw_type or round.draw_type
    try:
        if teams_in_debate in [1, 2, 4]:
            klass = DRAW_MANAGER_CLASSES[(teams_in_debate, draw_type)]
        else:
            klass = DRAW_MANAGER_CLASSES[(None, draw_type)]
    except KeyError:
        if teams_in_debate == 2:
            raise DrawUserError(_("The draw type %(type)s can't be used with two-team formats.") % {'type': round.get_draw_type_display()})
        elif teams_in_debate == 4:
            raise DrawUserError(_("The draw type %(type)s can't be used with British Parliamentary.") % {'type': round.get_draw_type_display()})
        else:
            raise DrawUserError(_("Unrecognised \"teams in debate\" option: %(option)s") % {'option': teams_in_debate})
    logger.debug("Using draw manager class: %s", klass.__name__)
    return klass(round, active_only)


class BaseDrawManager:
    """Creates, modifies and retrieves relevant Debate objects relating to a draw."""

    generator_type = None

    def __init__(self, round, active_only=True):
        self.round = round
        self.teams_in_debate = self.round.tournament.pref('teams_in_debate')
        self.active_only = active_only

    def get_relevant_options(self):
        if self.teams_in_debate == 2:
            return [
                "avoid_institution",
                "avoid_history",
                "history_penalty",
                "institution_penalty",
                "pullup_debates_penalty",
                "side_penalty",
                "pairing_penalty",
                "avoid_conflicts",
            ]
        return []

    def n_byes(self, n_teams):
        if self.get_bye_selection_mode() != 'off':
            if self.teams_in_debate == 1:
                return 0
            return n_teams % len(self.round.tournament.sides)
        return 0

    def get_bye_selection_mode(self):
        selection = self.round.tournament.pref('bye_team_selection')
        if selection == 'unmatched_team':
            # Backward compatibility for tournaments that still have the old value saved.
            self.round.tournament.preferences['draw_rules__bye_team_selection'] = 'middle_odd_bracket'
            return 'middle_odd_bracket'
        return selection

    def get_avoid_conflicts_mode(self):
        selection = self.round.tournament.pref('draw_avoid_conflicts')
        if selection == 'fold_after_pullups':
            # Backward compatibility for tournaments that still have the old value saved.
            self.round.tournament.preferences['draw_rules__draw_avoid_conflicts'] = 'one_up_one_down'
            return 'one_up_one_down'
        return selection

    def get_side_allocation_mode(self):
        return get_effective_side_allocation_mode(self.round)

    def get_generator_type(self):
        return self.generator_type

    def _get_draw_option_value(self, option):
        if option == "avoid_conflicts":
            return self.get_avoid_conflicts_mode()
        return self.round.tournament.preferences[OPTIONS_TO_CONFIG_MAPPING[option]]

    def _build_draw_options(self, options: dict | None = None) -> dict:
        resolved = dict(options or {})
        for key in self.get_relevant_options():
            if key not in resolved:
                resolved[key] = self._get_draw_option_value(key)

        if resolved.get("avoid_conflicts") == "fold_after_pullups":
            resolved["avoid_conflicts"] = "one_up_one_down"

        if "side_allocations" in resolved:
            resolved["side_allocations"] = self.get_side_allocation_mode()

        postallocate_sides = resolved.get("side_allocations") == "postallocated"
        if postallocate_sides and resolved.get("odd_bracket") in {"intermediate1", "intermediate2"}:
            raise DrawUserError(_("The odd-bracket method %(method)s requires side allocations before pairing.") % {
                "method": resolved["odd_bracket"],
            })
        if resolved.get("side_allocations") == "manual-ballot":
            resolved["side_allocations"] = "balance"
        elif postallocate_sides:
            resolved["side_allocations"] = "none"

        return resolved

    def _make_drawer(self, teams, options, results=None, rrseq=None, allow_odd_teams=False):
        return DrawGenerator(
            self.teams_in_debate,
            self.get_generator_type(),
            teams,
            results=results,
            rrseq=rrseq,
            allow_odd_teams=allow_odd_teams,
            **options,
        )

    def _get_draw_context(self):
        return self.get_results(), self.get_rrseq()

    def _prepare_generator_teams(self, teams, options):
        self._populate_side_history(teams)
        if options.get("side_allocations") == "preallocated":
            self._populate_team_side_allocations(teams)

    def _generate_pairings(self, teams, options, allow_odd_teams=False):
        results, rrseq = self._get_draw_context()
        self._prepare_generator_teams(teams, options)
        logger.debug("Using generator type: %s", self.get_generator_type())
        drawer = self._make_drawer(
            teams,
            options,
            results=results,
            rrseq=rrseq,
            allow_odd_teams=allow_odd_teams,
        )
        return drawer.generate()

    def _persist_generated_draw(self, pairings, byes, *, postallocate_sides):
        if postallocate_sides:
            self._apply_postallocated_sides(pairings)
            self._save_pairing_side_allocations(pairings)

        debates = self._make_debates(pairings)
        debates.extend(self._make_bye_debates(byes, max([p.room_rank for p in pairings], default=0)))

        self.round.draw_status = Round.Status.DRAFT
        self.round.save()

        return debates

    def _special_bye_selection(self, teams: List['Team'], n_byes: int):
        return None

    def _get_base_team_queryset(self):
        if self.active_only:
            return self.round.active_teams.all()
        return self.round.tournament.team_set.all()

    def _get_preallocated_split(self, teams: List['Team'], n_byes: int):
        if n_byes == 0 or self.get_side_allocation_mode() != 'preallocated':
            return None

        active_team_ids = [team.id for team in teams]
        allocated_ids = set(self.round.teamsideallocation_set.filter(team_id__in=active_team_ids).values_list('team_id', flat=True))
        if not allocated_ids:
            return None

        unallocated = [team for team in teams if team.id not in allocated_ids]
        if not unallocated:
            return None

        if len(unallocated) > n_byes:
            raise DrawUserError(_("There are too many active teams without side pre-allocations for %(round)s. Assign all debating teams, or leave exactly %(count)d team unassigned to receive the bye.") % {
                'round': self.round.name,
                'count': n_byes,
            })

        if len(unallocated) == n_byes:
            unallocated_ids = {team.id for team in unallocated}
            debating_teams = [team for team in teams if team.id not in unallocated_ids]
            return debating_teams, unallocated

        return None

    def _get_manual_bye_override_split(self, teams: List['Team'], n_byes: int):
        if n_byes != 1:
            return None

        try:
            override_team_id = self.round.bye_team_override.team_id
        except ByeTeamOverride.DoesNotExist:
            return None

        for team in teams:
            if team.id == override_team_id:
                debating_teams = [candidate for candidate in teams if candidate.id != override_team_id]
                return debating_teams, [team]

        return None

    def _split_teams_and_byes(self, teams: List['Team'], selector=None) -> Tuple[List['Team'], List['Team']]:
        n_byes = self.n_byes(len(teams))
        if not n_byes:
            return teams, []

        manual_override = self._get_manual_bye_override_split(teams, n_byes)
        if manual_override is not None:
            return manual_override

        preallocated = self._get_preallocated_split(teams, n_byes)
        if preallocated is not None:
            return preallocated

        special = self._special_bye_selection(teams, n_byes)
        if special is not None:
            return special

        if selector is not None:
            return selector(list(teams), n_byes)

        return teams[:-n_byes], teams[-n_byes:]

    def get_teams(self) -> Tuple[List['Team'], List['Team']]:
        teams = list(self._get_base_team_queryset())
        return self._split_teams_and_byes(teams)

    def get_results(self):
        # Only needed for EliminationDrawManager
        return None

    def get_rrseq(self):
        # Only needed for RoundRobinDrawManager
        return None

    def _populate_side_history(self, teams):
        sides = self.round.tournament.sides

        if self.round.prev:
            prev_seq = self.round.prev.seq
            side_history = get_side_history(teams, sides, prev_seq)
            for team in teams:
                team.side_history = side_history[team.id]
        else:
            for team in teams:
                team.side_history = [0] * len(sides)

    def _populate_team_side_allocations(self, teams):
        tsas = dict()
        for tsa in self.round.teamsideallocation_set.all():
            tsas[tsa.team] = tsa.side
        for team in teams:
            if team in tsas:
                team.allocated_side = tsas[team]

    def _apply_postallocated_sides(self, pairings: List['BasePairing']):
        apply_postallocated_sides(self.round, pairings)

    def _save_pairing_side_allocations(self, pairings: List['BasePairing']):
        sides = list(self.round.tournament.sides)
        allocations = []
        for pairing in pairings:
            for team, side in zip(pairing.teams, sides):
                allocations.append(TeamSideAllocation(round=self.round, team=team, side=side))

        self.round.teamsideallocation_set.all().delete()
        TeamSideAllocation.objects.bulk_create(allocations)

    def _choose_solo_auto_side(self, team, side_counts, allowed_sides):
        side_history = getattr(team, 'side_history', [0] * len(allowed_sides))
        history_by_side = dict(zip(allowed_sides, side_history))
        return min(allowed_sides, key=lambda side: (
            side_counts[side],
            history_by_side.get(side, 0),
            side,
        ))

    def _get_solo_side_allocations(self, pairings: List['BasePairing']):
        allowed_sides = list(self.round.tournament.sides)
        if not allowed_sides:
            raise DrawUserError(_("Solo speech draws require at least one available side."))

        saved_allocations = {
            tsa.team_id: tsa.side
            for tsa in self.round.teamsideallocation_set.all()
        }
        pairings_by_rank = sorted(pairings, key=lambda pairing: (pairing.room_rank, pairing.bracket))
        side_counts = Counter()
        allocations = {}
        missing_teams = []

        for pairing in pairings_by_rank:
            if len(pairing.teams) != 1:
                raise DrawUserError(_("Solo speech draws must have exactly one team in each debate."))

            team = pairing.teams[0]
            side = saved_allocations.get(team.id)
            if side is None:
                missing_teams.append(team)
                continue
            if side not in allowed_sides:
                raise DrawUserError(_("Assign a saved affirmative/negative side for every active team before generating this solo speech draw."))

            allocations[team.id] = side
            side_counts[side] += 1

        if missing_teams and not self.round.is_break_round:
            raise DrawUserError(_("Assign a saved affirmative/negative side for every active team before generating this solo speech draw."))

        new_allocations = []
        for team in missing_teams:
            side = self._choose_solo_auto_side(team, side_counts, allowed_sides)
            allocations[team.id] = side
            side_counts[side] += 1
            new_allocations.append(TeamSideAllocation(round=self.round, team=team, side=side))

        if new_allocations:
            TeamSideAllocation.objects.bulk_create(new_allocations)

        return allocations

    def _make_debates(self, pairings: List['BasePairing']) -> list[Debate]:
        random.shuffle(pairings)  # to avoid IDs indicating room ranks

        debates = {}
        debateteams = []
        solo_allocations = None

        if self.teams_in_debate == 1:
            solo_allocations = self._get_solo_side_allocations(pairings)

        for pairing in pairings:
            debate = Debate(round=self.round, bracket=pairing.bracket, room_rank=pairing.room_rank, flags=pairing.flags)
            if (self.round.tournament.pref('draw_side_allocations') == "manual-ballot" or
                    self.round.is_break_round):
                debate.sides_confirmed = False
            debates[pairing] = debate

        Debate.objects.bulk_create(debates.values())
        logger.debug("Created %d debates", len(debates))

        for pairing, debate in debates.items():
            if self.teams_in_debate == 1:
                team = pairing.teams[0]
                side = solo_allocations.get(team.id)

                dt = DebateTeam(debate=debate, team=team, side=side, flags=pairing.get_team_flags(team))
                debateteams.append(dt)
                continue

            for team, side in zip(pairing.teams, self.round.tournament.sides):
                dt = DebateTeam(debate=debate, team=team, side=side, flags=pairing.get_team_flags(team))
                debateteams.append(dt)

        DebateTeam.objects.bulk_create(debateteams)
        logger.debug("Created %d debate teams", len(debateteams))
        return list(debates.values())

    def _make_bye_debates(self, byes: List['Team'], room_rank: int) -> list[Debate]:
        """We'd want the room rank as to always show byes at the bottom"""
        debates = []
        for i, bye in enumerate(byes, start=room_rank + 1):
            debate = Debate(round=self.round, bracket=-1, room_rank=i)
            debate.save()
            debates.append(debate)

            dt = DebateTeam(debate=debate, team=bye, side=DebateSide.BYE)
            dt.save()

        if debates:
            refresh_bye_ballots(self.round.tournament, debates=debates)

        return debates

    def delete(self):
        self.round.debate_set.all().delete()

    def create(self, options: dict | None = None) -> list[Debate]:
        """Generates a draw and populates the database with it."""

        if self.round.draw_status != Round.Status.NONE:
            raise RuntimeError("Tried to create a draw on round that already has a draw")

        self.delete()

        options = self._build_draw_options(options)
        postallocate_sides = options.get("side_allocations") == "none" and self.get_side_allocation_mode() == "postallocated"

        teams, byes = self.get_teams()
        pairings = self._generate_pairings(teams, options)
        return self._persist_generated_draw(pairings, byes, postallocate_sides=postallocate_sides)


class RandomDrawManager(BaseDrawManager):
    generator_type = "random"

    def get_relevant_options(self):
        options = super().get_relevant_options()
        if self.teams_in_debate == 2:
            options.extend(["avoid_conflicts", "side_allocations"])
        return options

    def _special_bye_selection(self, teams: List['Team'], n_byes: int):
        selection = self.get_bye_selection_mode()
        if selection != 'middle_odd_bracket':
            return None
        candidates = list(teams)
        byes = []
        for i in range(n_byes):
            byes.append(candidates.pop(random.randrange(len(candidates))))
        return candidates, byes


class ManualDrawManager(BaseDrawManager):
    generator_type = "manual"

    def get_relevant_options(self):
        return []


class PowerPairedDrawManager(BaseDrawManager):
    generator_type = "power_paired"

    def get_relevant_options(self):
        options = super().get_relevant_options()
        if self.teams_in_debate == 2:
            options.extend([
                "avoid_conflicts", "odd_bracket", "pairing_method",
                "pullup_restriction", "side_allocations",
                "max_times_on_one_side", "pullup_penalty",
            ])
        elif self.teams_in_debate == 4:
            options.extend(["pullup", "position_cost", "assignment_method", "renyi_order", "exponent"])
        return options

    def _get_ranked_teams(self) -> List['Team']:
        """Get teams in ranked order."""
        teams = self.round.tournament.team_set.filter(id__in=self._get_base_team_queryset().values('id'))

        metrics = self.round.tournament.pref('team_standings_precedence')
        pullup_metric = BasePowerPairedDrawGenerator.PULLUP_RESTRICTION_METRICS[self.round.tournament.pref('draw_pullup_restriction')]
        extra_metrics = {pullup_metric} if pullup_metric is not None else set()

        pullup_debates_penalty = self.round.tournament.pref("pullup_debates_penalty")
        if pullup_debates_penalty > 0:
            extra_metrics.add("pullup_debates")
        if self.round.tournament.pref("draw_odd_bracket") == 'pullup_lowest_ds_rank_npulls':
            extra_metrics |= {'npullups', 'draw_strength_rank'}
        extra_metrics -= set(metrics)

        generator = TeamStandingsGenerator(metrics, ('rank', 'subrank'), tiebreak="random", extra_metrics=list(extra_metrics))
        standings = generator.generate(teams, round=self.round.prev)

        ranked = []
        for standing in standings:
            team = standing.team
            team.points = next(standing.itermetrics(), 0) or 0
            team.subrank = standing.get_ranking('subrank')
            if pullup_debates_penalty > 0:
                team.pullup_debates = standing.metrics.get("pullup_debates", 0)
            if pullup_metric:
                setattr(team, pullup_metric, standing.metrics[pullup_metric])
            if self.round.tournament.pref("draw_odd_bracket") == 'pullup_lowest_ds_rank_npulls':
                team.npullups = standing.metrics.get('npullups')
                team.draw_strength_rank = standing.metrics.get('draw_strength_rank')

            ranked.append(team)

        return ranked

    def _can_generate_bye_from_draw(self, n_byes: int, options: dict | None = None) -> bool:
        if self.get_bye_selection_mode() != 'middle_odd_bracket':
            return False
        if self.teams_in_debate != 2 or n_byes != 1:
            return False

        resolved = self._build_draw_options(options)
        if resolved.get("avoid_conflicts") == 'graph_one':
            return False
        return True

    def _generate_pairings_and_byes_from_draw(self, teams: List['Team'], options: dict | None = None):
        resolved = self._build_draw_options(options)
        self._prepare_generator_teams(teams, resolved)
        if resolved.get("side_allocations") == "preallocated":
            missing_allocations = [team for team in teams if not hasattr(team, "allocated_side")]
            if missing_allocations:
                raise DrawUserError(_("Assign saved sides for every active team before using this bye-selection method with pre-allocated sides."))

        results, rrseq = self._get_draw_context()
        drawer = self._make_drawer(teams, resolved, results=results, rrseq=rrseq, allow_odd_teams=True)
        if not hasattr(drawer, 'generate_with_bye'):
            raise DrawUserError(_("This bye-selection method isn't supported for this draw configuration."))
        pairings, bye_team = drawer.generate_with_bye()
        return pairings, [bye_team], resolved

    def get_teams(self) -> Tuple[List['Team'], List['Team']]:
        ranked = self._get_ranked_teams()
        n_byes = self.n_byes(len(ranked))
        if n_byes:
            manual_override = self._get_manual_bye_override_split(ranked, n_byes)
            if manual_override is not None:
                return manual_override

            if self._can_generate_bye_from_draw(n_byes):
                _, byes, _ = self._generate_pairings_and_byes_from_draw(ranked)
                bye_ids = {team.id for team in byes}
                return [team for team in ranked if team.id not in bye_ids], byes

            preallocated = self._get_preallocated_split(ranked, n_byes)
            if preallocated is not None:
                return preallocated

            special = self._special_bye_selection(ranked, n_byes)
            if special is not None:
                return special

        def select_byes(candidates, n_byes):
            selection = self.get_bye_selection_mode()
            if selection == 'random':
                byes = []
                for i in range(n_byes):
                    byes.append(candidates.pop(random.randrange(len(candidates))))
                return candidates, byes
            elif selection == 'lowest':
                return candidates[:-n_byes], candidates[-n_byes:]
            else:
                raise RuntimeError("Bye team(s) created without recognized selection option")

        return self._split_teams_and_byes(ranked, selector=select_byes)

    def create(self, options: dict | None = None) -> list[Debate]:
        if self.round.draw_status != Round.Status.NONE:
            raise RuntimeError("Tried to create a draw on round that already has a draw")

        self.delete()

        resolved = self._build_draw_options(options)
        postallocate_sides = resolved.get("side_allocations") == "none" and self.get_side_allocation_mode() == "postallocated"
        ranked = self._get_ranked_teams()
        n_byes = self.n_byes(len(ranked))

        pairings = None
        byes: List['Team'] = []

        if n_byes:
            manual_override = self._get_manual_bye_override_split(ranked, n_byes)
            if manual_override is not None:
                teams, byes = manual_override
            elif self._can_generate_bye_from_draw(n_byes, resolved):
                pairings, byes, resolved = self._generate_pairings_and_byes_from_draw(ranked, resolved)
                teams = [team for team in ranked if team.id not in {bye.id for bye in byes}]
            else:
                teams, byes = self.get_teams()
        else:
            teams = ranked

        if pairings is None:
            logger.debug("Using generator type: %s", self.get_generator_type())
            pairings = self._generate_pairings(teams, resolved)

        return self._persist_generated_draw(pairings, byes, postallocate_sides=postallocate_sides)

    def _special_bye_selection(self, teams: List['Team'], n_byes: int):
        selection = self.get_bye_selection_mode()
        if selection != 'middle_odd_bracket':
            return None

        if self.teams_in_debate != 2 or n_byes != 1:
            raise DrawUserError(_("This bye-selection method is only supported for one bye in two-team preliminary draws."))

        if self.get_avoid_conflicts_mode() == 'graph_one':
            raise DrawUserError(_("This bye-selection method isn't supported with the conflict-avoidance method that determines pullups itself."))

        raise DrawUserError(_("This bye-selection method isn't supported for this draw configuration."))


class SeededDrawManager(BaseDrawManager):
    generator_type = "power_paired"

    def get_relevant_options(self):
        options = super().get_relevant_options()
        if self.teams_in_debate == 2:
            options.extend(["avoid_conflicts", "pairing_method", "side_allocations"])
        elif self.teams_in_debate == 4:
            options.extend(["assignment_method"])
        return options

    def _special_bye_selection(self, teams: List['Team'], n_byes: int):
        if self.get_bye_selection_mode() == 'middle_odd_bracket':
            raise DrawUserError(_("This bye-selection method isn't supported for seeded draws."))
        return None

    def get_teams(self) -> Tuple[List['Team'], List['Team']]:
        """Get teams in seeded order."""
        teams = list(self._get_base_team_queryset())
        random.shuffle(teams)
        teams.sort(key=lambda t: -t.seed)

        def select_byes(candidates, n_byes):
            if self.get_bye_selection_mode() == 'lowest':
                return candidates[:-n_byes], candidates[-n_byes:]

            byes = []
            for i in range(n_byes):
                byes.append(candidates.pop(random.randrange(len(candidates))))
            return candidates, byes

        teams, byes = self._split_teams_and_byes(teams, selector=select_byes)

        for team in teams:
            team.points = 0
            team.subrank = team.seed + 1

        return teams, byes


class RoundRobinDrawManager(BaseDrawManager):
    generator_type = "round_robin"

    def get_rrseq(self):
        prior_rrs = list(self.round.tournament.round_set.filter(draw_type=Round.DrawType.ROUNDROBIN).order_by('seq'))
        try:
            rr_seq = prior_rrs.index(self.round) + 1 # Dont 0-index
        except ValueError:
            raise RuntimeError("Tried to calculate an effective round robin seq but couldn't")

        return rr_seq


class BaseEliminationDrawManager(BaseDrawManager):
    result_pairing_class = None

    def get_teams(self) -> Tuple[List['Team'], List['Team']]:
        breaking_teams = self.round.break_category.breakingteam_set_competing.order_by(
                'break_rank').select_related('team')
        return [bt.team for bt in breaking_teams], []

    def get_results(self):
        if self.round.prev is not None and self.round.prev.is_break_round:
            debates = self.round.prev.debate_set_with_prefetches(ordering=('room_rank',), results=True,
                    adjudicators=False, speakers=False, venues=False)
            pairings = [self.result_pairing_class.from_debate(debate, tournament=self.round.tournament)
                        for debate in debates]
            return pairings
        else:
            return None


class EliminationDrawManager(BaseEliminationDrawManager):
    result_pairing_class = ResultPairing

    def get_generator_type(self):
        if self.round.prev is not None and self.round.prev.is_break_round:
            return "elimination"
        else:
            return "first_elimination"


class SoloEliminationDrawManager(BaseEliminationDrawManager):

    def get_results(self):
        return None

    def get_generator_type(self):
        return "elimination"


class BPEliminationDrawManager(BaseEliminationDrawManager):
    result_pairing_class = BPEliminationResultPairing

    def get_generator_type(self):
        break_size = self.round.break_category.break_size
        if break_size % 6 == 0 and ispow2(break_size // 6):
            nprev_rounds = self.round.break_category.round_set.filter(seq__lt=self.round.seq).count()
            if nprev_rounds == 0:
                return "partial_elimination"
            elif nprev_rounds == 1:
                return "after_partial_elimination"
            else:
                return "elimination"
        elif break_size % 4 == 0 and ispow2(break_size // 4):
            if self.round.prev is not None and self.round.prev.is_break_round:
                return "elimination"
            else:
                return "first_elimination"
        else:
            raise DrawUserError(_("The break size (%(size)d) for this break category was invalid. "
                "It must be either six times or four times a power of two.") % {'size': break_size})


DRAW_MANAGER_CLASSES = {
    (1, Round.DrawType.RANDOM): RandomDrawManager,
    (1, Round.DrawType.POWERPAIRED): PowerPairedDrawManager,
    (1, Round.DrawType.MANUAL): ManualDrawManager,
    (1, Round.DrawType.ELIMINATION): SoloEliminationDrawManager,
    (2, Round.DrawType.RANDOM): RandomDrawManager,
    (2, Round.DrawType.POWERPAIRED): PowerPairedDrawManager,
    (2, Round.DrawType.ROUNDROBIN): RoundRobinDrawManager,
    (2, Round.DrawType.MANUAL): ManualDrawManager,
    (2, Round.DrawType.ELIMINATION): EliminationDrawManager,
    (2, Round.DrawType.SEEDED): SeededDrawManager,
    (4, Round.DrawType.RANDOM): RandomDrawManager,
    (4, Round.DrawType.MANUAL): ManualDrawManager,
    (4, Round.DrawType.POWERPAIRED): PowerPairedDrawManager,
    (4, Round.DrawType.ELIMINATION): BPEliminationDrawManager,
    (None, Round.DrawType.RANDOM): RandomDrawManager,
    (None, Round.DrawType.MANUAL): ManualDrawManager,
    (None, Round.DrawType.ELIMINATION): EliminationDrawManager,
}
