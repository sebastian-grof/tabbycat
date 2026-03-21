from django.utils.translation import gettext as _

from .generator import DrawUserError


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
            continue

        if left_side is not None and left_side == right_side:
            raise DrawUserError(_(
                "Saved side allocations for %(round)s can't be applied after pairing because %(team1)s and %(team2)s both require the same side."
            ) % {
                "round": round.name,
                "team1": getattr(left, "short_name", str(left)),
                "team2": getattr(right, "short_name", str(right)),
            })

        if left_side == sides[0] or right_side == sides[1]:
            continue
        if left_side == sides[1] or right_side == sides[0]:
            pairing.teams.reverse()
