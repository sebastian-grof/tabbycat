from django.utils.translation import gettext as _

from .generator import DrawUserError


def _balance_pairing(pairing):
    if hasattr(pairing, "balance_sides"):
        try:
            pairing.balance_sides()
            return
        except AttributeError:
            pass

    if hasattr(pairing, "shuffle_sides"):
        pairing.shuffle_sides()


def apply_postallocated_sides(round, pairings, allocations=None):
    sides = list(round.tournament.sides)
    if len(sides) != 2:
        raise DrawUserError(_("Post-pairing side allocations are only supported in two-team formats."))

    if allocations is None:
        allocations = {
            tsa.team_id: tsa.side
            for tsa in round.teamsideallocation_set.all()
        }

    for pairing in pairings:
        left, right = pairing.teams
        left_side = allocations.get(left.id)
        right_side = allocations.get(right.id)

        if left_side is None and right_side is None:
            _balance_pairing(pairing)
            continue

        if left_side is not None and right_side is not None:
            if left_side == right_side:
                _balance_pairing(pairing)
                continue
            if left_side == sides[1] and right_side == sides[0]:
                pairing.teams.reverse()
            continue

        if left_side is not None:
            if left_side == sides[1]:
                pairing.teams.reverse()
            continue

        if right_side is not None:
            if right_side == sides[0]:
                pairing.teams.reverse()
            continue
