from collections import Counter
import random

from django.utils.translation import gettext as _

from .generator import DrawUserError
from .manager import DrawManager
from .models import TeamSideAllocation


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
    if round.tournament.pref('bye_team_selection') != 'off' and len(round.tournament.sides) > 0:
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


def get_round_allocations(round):
    return {
        tsa.team_id: tsa.side
        for tsa in round.teamsideallocation_set.all().order_by("team__short_name", "team__id")
    }


def summarize_allocations(round, allocations=None):
    allocations = allocations if allocations is not None else get_round_allocations(round)
    groups = get_round_team_groups(round)
    sides = list(round.tournament.sides)
    draw_team_ids = {team.id for team in groups["draw_teams"]}

    counts = Counter(
        side for team_id, side in allocations.items()
        if team_id in draw_team_ids and side is not None
    )
    assigned = sum(1 for team in groups["draw_teams"] if allocations.get(team.id) is not None)
    missing = len(groups["draw_teams"]) - assigned
    extra_assigned = sum(
        1 for team_id, side in allocations.items()
        if side is not None and team_id not in draw_team_ids
    )
    balanced = len(sides) == 2 and counts.get(sides[0], 0) == counts.get(sides[1], 0)

    return {
        "assigned": assigned,
        "missing": missing,
        "counts": counts,
        "balanced": balanced,
        "draw_team_count": len(groups["draw_teams"]),
        "bye_team_count": len(groups["bye_teams"]),
        "bye_teams": groups["bye_teams"],
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


def generate_random_allocations(round):
    sides = _get_two_team_sides(round.tournament)
    groups = get_round_team_groups(round)
    teams = groups["draw_teams"]

    if not teams:
        raise SideAllocationError(_("There are no available debating teams for this round yet."))
    if len(teams) % 2 != 0:
        raise SideAllocationError(_("The round still has an odd number of debating teams after accounting for byes. Check availability or bye settings before generating side allocations."))

    shuffled_team_ids = [team.id for team in teams]
    random.shuffle(shuffled_team_ids)
    halfway = len(shuffled_team_ids) // 2
    allocations = {team_id: sides[0] for team_id in shuffled_team_ids[:halfway]}
    allocations.update({team_id: sides[1] for team_id in shuffled_team_ids[halfway:]})
    replace_round_allocations(round, allocations)
    return allocations


def generate_opposite_allocations(round, source_round):
    if round.tournament_id != source_round.tournament_id:
        raise SideAllocationError(_("The source round must belong to the same tournament."))
    if round == source_round:
        raise SideAllocationError(_("The source round must be different from the target round."))

    sides = _get_two_team_sides(round.tournament)
    target_groups = get_round_team_groups(round)
    target_teams = target_groups["draw_teams"]
    source_allocations = get_round_allocations(source_round)
    opposite_by_side = {sides[0]: sides[1], sides[1]: sides[0]}

    target_side_count = len(target_teams) // 2
    allocations = {}
    missing_teams = []

    for team in target_teams:
        current_side = source_allocations.get(team.id)
        if current_side is None:
            missing_teams.append(team)
            continue
        if current_side not in opposite_by_side:
            raise SideAllocationError(_("Round %(round)s has an invalid side allocation.") % {
                "round": source_round.name,
            })
        allocations[team.id] = opposite_by_side[current_side]

    counts = Counter(allocations.values())
    remaining_slots = []
    for side in sides:
        remaining = target_side_count - counts.get(side, 0)
        if remaining < 0:
            raise SideAllocationError(_("Round %(round)s does not have usable side allocations for the teams debating there.") % {
                "round": source_round.name,
            })
        remaining_slots.extend([side] * remaining)

    if len(remaining_slots) != len(missing_teams):
        raise SideAllocationError(_("Round %(round)s does not have usable side allocations for the teams debating there.") % {
            "round": source_round.name,
        })

    random.shuffle(remaining_slots)
    for team, side in zip(missing_teams, remaining_slots):
        allocations[team.id] = side

    replace_round_allocations(round, allocations)
    return allocations
