import logging
from collections import Counter
from itertools import combinations
import random

from django.utils.translation import gettext as _

from .generator import DrawUserError
from .manager import DrawManager
from .models import ByeTeamOverride, TeamSideAllocation
from .types import DebateSide

logger = logging.getLogger(__name__)


class SideAllocationError(Exception):
    pass


def _team_sort_key(team):
    return (team.short_name, team.id)


def _get_two_team_sides(tournament):
    sides = list(tournament.sides)
    if len(sides) != 2:
        raise SideAllocationError(_("Side pre-allocation tools only support two-team formats."))
    return sides


def _get_teams_for_tournament(tournament):
    return list(tournament.team_set.order_by("short_name", "id"))


def _fallback_draw_split(round):
    teams = list(round.active_teams.order_by("short_name", "id"))
    if round.tournament.pref('teams_in_debate') == 1:
        n_byes = 0
    elif round.tournament.pref('bye_team_selection') != 'off' and len(round.tournament.sides) > 0:
        n_byes = len(teams) % len(round.tournament.sides)
    else:
        n_byes = 0
    if n_byes:
        return teams[:-n_byes], teams[-n_byes:]
    return teams, []


def get_round_team_groups(round):
    all_teams = _get_teams_for_tournament(round.tournament)
    active_teams = list(round.active_teams.order_by("short_name", "id"))
    active_team_ids = {team.id for team in active_teams}
    unavailable_teams = [team for team in all_teams if team.id not in active_team_ids]

    try:
        draw_teams, bye_teams = DrawManager(round, active_only=True).get_teams()
    except DrawUserError:
        draw_teams, bye_teams = _fallback_draw_split(round)

    draw_team_ids = {team.id for team in draw_teams}
    bye_team_ids = {team.id for team in bye_teams}

    return {
        "all_teams": all_teams,
        "active_teams": active_teams,
        "draw_teams": sorted((team for team in active_teams if team.id in draw_team_ids), key=_team_sort_key),
        "bye_teams": sorted((team for team in active_teams if team.id in bye_team_ids), key=_team_sort_key),
        "unavailable_teams": unavailable_teams,
    }


def get_bye_override_team(round):
    try:
        return round.bye_team_override.team
    except ByeTeamOverride.DoesNotExist:
        return None


def replace_bye_override(round, team):
    if team is None:
        ByeTeamOverride.objects.filter(round=round).delete()
        return

    ByeTeamOverride.objects.update_or_create(round=round, defaults={"team": team})


def get_round_allocations(round):
    return {
        tsa.team_id: tsa.side
        for tsa in round.teamsideallocation_set.all().order_by("team__short_name", "team__id")
    }


def summarize_allocations(round, allocations=None):
    allocations = allocations if allocations is not None else get_round_allocations(round)
    groups = get_round_team_groups(round)
    sides = list(round.tournament.sides)
    active_team_ids = {team.id for team in groups["active_teams"]}

    counts = Counter(
        side for team_id, side in allocations.items()
        if team_id in active_team_ids and side is not None
    )
    assigned = sum(1 for team in groups["active_teams"] if allocations.get(team.id) is not None)
    missing = len(groups["active_teams"]) - assigned
    extra_assigned = sum(
        1 for team_id, side in allocations.items()
        if side is not None and team_id not in active_team_ids
    )
    balanced = False
    if len(sides) == 2 and missing == 0:
        balanced = any(
            all(counts.get(side, 0) == candidate[side] for side in sides)
            for candidate in _candidate_side_counts(len(groups["active_teams"]), sides)
        )

    return {
        "assigned": assigned,
        "missing": missing,
        "counts": counts,
        "balanced": balanced,
        "active_team_count": len(groups["active_teams"]),
        "simulated_bye_team_count": len(groups["bye_teams"]),
        "simulated_bye_teams": groups["bye_teams"],
        "unavailable_team_count": len(groups["unavailable_teams"]),
        "unavailable_teams": groups["unavailable_teams"],
        "extra_assigned": extra_assigned,
    }


def replace_round_allocations(round, allocations):
    round.teamsideallocation_set.all().delete()
    TeamSideAllocation.objects.bulk_create([
        TeamSideAllocation(round=round, team_id=team_id, side=side)
        for team_id, side in allocations.items()
        if side is not None
    ])


def _get_generation_target_teams(round):
    return list(round.active_teams.order_by("short_name", "id"))


def _candidate_side_counts(total_teams, sides):
    base = total_teams // 2
    if total_teams % 2 == 0:
        return [{sides[0]: base, sides[1]: base}]
    return [
        {sides[0]: base + 1, sides[1]: base},
        {sides[0]: base, sides[1]: base + 1},
    ]


def _choose_target_side_counts(total_teams, sides, existing_counts=None):
    existing_counts = Counter(existing_counts or {})
    candidates = [
        counts
        for counts in _candidate_side_counts(total_teams, sides)
        if all(existing_counts.get(side, 0) <= counts[side] for side in sides)
    ]
    if not candidates:
        raise SideAllocationError(_("The available teams can't be split into valid saved side allocations for this round."))

    if len(candidates) > 1 and existing_counts.get(sides[0], 0) != existing_counts.get(sides[1], 0):
        preferred_side = sides[0] if existing_counts[sides[0]] > existing_counts[sides[1]] else sides[1]
        preferred = [
            counts for counts in candidates
            if counts[preferred_side] > counts[sides[0] if preferred_side == sides[1] else sides[1]]
        ]
        if preferred:
            candidates = preferred

    return random.choice(candidates)


def _ordered_target_side_counts(total_teams, sides, existing_counts=None):
    existing_counts = Counter(existing_counts or {})
    candidates = [
        counts
        for counts in _candidate_side_counts(total_teams, sides)
        if all(existing_counts.get(side, 0) <= counts[side] for side in sides)
    ]
    if not candidates:
        raise SideAllocationError(_("The available teams can't be split into valid saved side allocations for this round."))

    if len(candidates) == 1:
        return candidates

    if existing_counts.get(sides[0], 0) != existing_counts.get(sides[1], 0):
        preferred_side = sides[0] if existing_counts[sides[0]] > existing_counts[sides[1]] else sides[1]
        candidates.sort(
            key=lambda counts: (
                counts[preferred_side] == counts[sides[0] if preferred_side == sides[1] else sides[1]],
                -counts[preferred_side],
            )
        )
        return candidates

    return sorted(candidates, key=lambda counts: counts[sides[1]], reverse=True)


def _fallback_target_brackets(target_teams):
    ordered = sorted(target_teams, key=_team_sort_key)
    return [ordered] if ordered else []


def _get_ranked_target_brackets(round, target_teams):
    team_map = {team.id: team for team in target_teams}
    manager = DrawManager(round, active_only=True)

    if not hasattr(manager, "_get_ranked_teams"):
        return _fallback_target_brackets(target_teams)

    try:
        ranked = manager._get_ranked_teams()
    except DrawUserError as exc:
        logger.warning(
            "Falling back to alphabetical target brackets for side allocation generation in round %s: %s",
            round.id,
            exc,
        )
        return _fallback_target_brackets(target_teams)

    ranked = [team for team in ranked if team.id in team_map]
    if not ranked:
        return _fallback_target_brackets(target_teams)

    brackets = []
    last_points = object()
    for team in ranked:
        points = team.points
        if not brackets or points != last_points:
            brackets.append([])
            last_points = points
        brackets[-1].append(team_map[team.id])
    return brackets


def _assign_missing_opposite_sides_by_bracket(round, target_teams, allocations, missing_teams, sides):
    if not missing_teams:
        return allocations

    selector = _get_preallocated_pullup_selector(round)
    if selector is None:
        return _assign_missing_opposite_sides_by_static_bracket_balance(round, target_teams, allocations, missing_teams, sides)

    existing_counts = Counter(allocations.values())
    brackets = _get_ranked_target_brackets(round, target_teams)
    global_targets = _ordered_target_side_counts(len(target_teams), sides, existing_counts)
    best_choice = None

    for target_index, target_counts in enumerate(global_targets):
        required_aff = target_counts[sides[0]] - existing_counts.get(sides[0], 0)
        if required_aff < 0 or required_aff > len(missing_teams):
            continue

        for aff_indices in combinations(range(len(missing_teams)), required_aff):
            aff_index_set = set(aff_indices)
            candidate = dict(allocations)
            for index, team in enumerate(missing_teams):
                candidate[team.id] = sides[0] if index in aff_index_set else sides[1]

            penalties = _simulate_sequential_pullup_penalties(brackets, candidate, sides, selector)
            if penalties is None:
                continue

            key = penalties + (target_index,)
            if best_choice is None or key < best_choice[0]:
                best_choice = (key, candidate)

    if best_choice is None:
        return _assign_missing_opposite_sides_by_static_bracket_balance(round, target_teams, allocations, missing_teams, sides)

    return best_choice[1]


def _get_preallocated_pullup_selector(round):
    odd_bracket = round.tournament.pref('draw_odd_bracket')
    if odd_bracket == 'pullup_top':
        return lambda pool, count: pool[:count]
    if odd_bracket == 'pullup_bottom':
        return lambda pool, count: pool[-count:]
    if odd_bracket == 'pullup_random':
        def random_selector(pool, count):
            selected = set(random.sample(range(len(pool)), count))
            return [team for index, team in enumerate(pool) if index in selected]
        return random_selector
    return None


def _simulate_sequential_pullup_penalties(brackets, allocations, sides, selector):
    needed_side = None
    needed_count = 0
    penalties = []

    for bracket in brackets:
        remaining = list(bracket)
        if needed_count:
            matching_side = [team for team in remaining if allocations.get(team.id) == needed_side]
            if len(matching_side) < needed_count:
                return None
            pulled = selector(matching_side, needed_count)
            pulled_ids = {team.id for team in pulled}
            remaining = [team for team in remaining if team.id not in pulled_ids]

        aff_count = sum(1 for team in remaining if allocations.get(team.id) == sides[0])
        neg_count = sum(1 for team in remaining if allocations.get(team.id) == sides[1])
        penalties.append(abs(abs(aff_count - neg_count) - (len(remaining) % 2)))

        if aff_count > neg_count:
            needed_side = sides[1]
            needed_count = aff_count - neg_count
        elif neg_count > aff_count:
            needed_side = sides[0]
            needed_count = neg_count - aff_count
        else:
            needed_side = None
            needed_count = 0

    return tuple(penalties)


def _assign_missing_opposite_sides_by_static_bracket_balance(round, target_teams, allocations, missing_teams, sides):
    if not missing_teams:
        return allocations

    missing_ids = {team.id for team in missing_teams}
    existing_counts = Counter(allocations.values())
    brackets = _get_ranked_target_brackets(round, target_teams)
    bracket_options = []

    for bracket in brackets:
        bracket_missing = [team for team in bracket if team.id in missing_ids]
        if not bracket_missing:
            bracket_options.append([{"aff_assigned": 0, "penalty": 0, "teams": []}])
            continue

        fixed_counts = Counter(
            allocations[team.id]
            for team in bracket
            if allocations.get(team.id) is not None
        )
        options = []
        for aff_assigned in range(len(bracket_missing) + 1):
            neg_assigned = len(bracket_missing) - aff_assigned
            final_aff = fixed_counts.get(sides[0], 0) + aff_assigned
            final_neg = fixed_counts.get(sides[1], 0) + neg_assigned
            ideal_diff = len(bracket) % 2
            penalty = abs(abs(final_aff - final_neg) - ideal_diff)
            options.append({
                "aff_assigned": aff_assigned,
                "penalty": penalty,
                "teams": bracket_missing,
            })
        bracket_options.append(options)

    global_targets = _ordered_target_side_counts(len(target_teams), sides, existing_counts)
    best_choice = None

    for target_index, target_counts in enumerate(global_targets):
        required_aff = target_counts[sides[0]] - existing_counts.get(sides[0], 0)
        states = {0: ((), [])}

        for options in bracket_options:
            next_states = {}
            for used_aff, (penalties, choices) in states.items():
                for option in options:
                    new_aff = used_aff + option["aff_assigned"]
                    new_penalties = penalties + (option["penalty"],)
                    new_choices = choices + [option]
                    current = next_states.get(new_aff)
                    if current is None or new_penalties < current[0]:
                        next_states[new_aff] = (new_penalties, new_choices)
            states = next_states

        if required_aff not in states:
            continue

        penalties, choices = states[required_aff]
        key = penalties + (target_index,)
        if best_choice is None or key < best_choice[0]:
            best_choice = (key, choices)

    if best_choice is None:
        raise SideAllocationError(_("Round %(round)s does not have usable side allocations for the teams debating there.") % {
            "round": round.name,
        })

    resolved = dict(allocations)
    for option in best_choice[1]:
        bracket_missing = sorted(option["teams"], key=lambda team: getattr(team, "subrank", 0) or 0)
        for team in bracket_missing[:option["aff_assigned"]]:
            resolved[team.id] = sides[0]
        for team in bracket_missing[option["aff_assigned"]:]:
            resolved[team.id] = sides[1]

    return resolved


def generate_random_allocations(round):
    sides = _get_two_team_sides(round.tournament)
    teams = _get_generation_target_teams(round)

    if not teams:
        raise SideAllocationError(_("There are no available teams for this round yet."))
    if round.tournament.pref('teams_in_debate') != 1 and round.tournament.pref('bye_team_selection') == 'off' and len(teams) % 2 != 0:
        raise SideAllocationError(_("The round still has an odd number of debating teams after accounting for byes. Check availability or bye settings before generating side allocations."))

    shuffled_team_ids = [team.id for team in teams]
    random.shuffle(shuffled_team_ids)
    target_counts = _choose_target_side_counts(len(shuffled_team_ids), sides)
    remaining_slots = []
    for side in sides:
        remaining_slots.extend([side] * target_counts[side])
    random.shuffle(remaining_slots)

    allocations = {team_id: side for team_id, side in zip(shuffled_team_ids, remaining_slots)}
    replace_round_allocations(round, allocations)
    return allocations


def _generate_uniform_allocations(round, side_index):
    sides = _get_two_team_sides(round.tournament)
    teams = _get_generation_target_teams(round)

    if not teams:
        raise SideAllocationError(_("There are no available teams for this round yet."))

    side = sides[side_index]
    allocations = {team.id: side for team in teams}
    replace_round_allocations(round, allocations)
    return allocations


def generate_all_affirmation_allocations(round):
    return _generate_uniform_allocations(round, 0)


def generate_all_negation_allocations(round):
    return _generate_uniform_allocations(round, 1)


def generate_opposite_allocations(round, source_round):
    if round.tournament_id != source_round.tournament_id:
        raise SideAllocationError(_("The source round must belong to the same tournament."))
    if round == source_round:
        raise SideAllocationError(_("The source round must be different from the target round."))

    sides = _get_two_team_sides(round.tournament)
    target_teams = _get_generation_target_teams(round)
    source_allocations = get_round_allocations(source_round)
    source_actual_sides = {
        debateteam.team_id: debateteam.side
        for debate in source_round.debate_set.prefetch_related('debateteam_set')
        for debateteam in debate.debateteam_set.all()
        if debateteam.side != DebateSide.BYE
    }
    source_has_draw = source_round.debate_set.exists()
    opposite_by_side = {sides[0]: sides[1], sides[1]: sides[0]}

    allocations = {}
    missing_teams = []

    for team in target_teams:
        current_side = source_actual_sides.get(team.id) if source_has_draw else source_allocations.get(team.id)
        if current_side is None:
            missing_teams.append(team)
            continue
        if current_side not in opposite_by_side:
            raise SideAllocationError(_("Round %(round)s has an invalid side allocation.") % {
                "round": source_round.name,
            })
        allocations[team.id] = opposite_by_side[current_side]

    allocations = _assign_missing_opposite_sides_by_bracket(round, target_teams, allocations, missing_teams, sides)

    replace_round_allocations(round, allocations)
    return allocations
