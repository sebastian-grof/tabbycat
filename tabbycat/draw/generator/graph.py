from collections import OrderedDict
from typing import Optional, TYPE_CHECKING

import munkres
import networkx as nx
from django.utils.translation import gettext as _

from .common import DrawUserError
from ..types import DebateSide

if TYPE_CHECKING:
    from participants.models import Team


def sign(n: int) -> int:
    """Sign function for integers, -1, 0, or 1"""
    try:
        return n // abs(n)
    except ZeroDivisionError:
        return 0


class GraphGeneratorMixin:
    def avoid_conflicts(self, pairings):
        """Graph optimisation avoids conflicts, so method is extraneous."""
        pass

    def assignment_cost(self, t1, t2, size, bracket=None) -> Optional[int]:
        if t1 is t2:  # Same team
            return

        penalty = 0
        if self.options["avoid_history"]:
            penalty += t1.seen(t2) * self.options["history_penalty"]
        if self.options["avoid_institution"] and t1.same_institution(t2):
            penalty += self.options["institution_penalty"]

        # Add penalty of a side imbalance
        if self.options["side_allocations"] == "balance" and self.options["side_penalty"] > 0:
            t1_affs, t1_negs = t1.side_history
            t2_affs, t2_negs = t2.side_history

            if self.options["max_times_on_one_side"] > 0:
                if max(t1_affs, t1_negs, t2_affs, t1_negs) > self.options["max_times_on_one_side"]:
                    return None

            # Only declare an imbalance if both sides have been on the same side more often
            # Affs are positive, negs are negative. If teams have opposite signs, negative imbalance
            # gets reduced to 0. Equalities have no restriction on the side to be allocated so
            # cancel as well. neg*neg -> pos
            imbalance = max(0, sign(t1_affs - t1_negs) * sign(t2_affs - t2_negs))

            # Get median imbalance between the two as a coefficient for the penalty to apply
            # This would prefer an imbalance of (+5 - +1) becoming (+4 - +2) rather than
            # (+5 - +4) becoming (+4 - +5), in a severe case.
            magnitude = (abs(t1_affs - t1_negs) + abs(t2_affs - t2_negs)) // 2

            penalty += imbalance * magnitude * self.options["side_penalty"]

        return penalty

    def get_n_teams(self, teams: list['Team']) -> int:
        return len(teams)

    def _compute_matching(self, teams, bracket=None):
        graph = nx.Graph()
        n_teams = self.get_n_teams(teams)
        for k, t1 in enumerate(teams):
            for t2 in teams[k+1:]:
                penalty = self.assignment_cost(t1, t2, n_teams, bracket)
                if penalty is not None:
                    graph.add_edge(t1, t2, weight=penalty)

        matching = nx.min_weight_matching(graph)
        if len(matching) * 2 != len(teams):
            raise DrawUserError(_("Couldn't find a complete matching for bye selection."))

        total_cost = sum(graph[t1][t2]["weight"] for t1, t2 in matching)
        return matching, total_cost

    def get_unmatched_team(self, teams, bracket=None):
        if len(teams) % 2 == 0:
            raise DrawUserError(_("Unmatched-team bye selection requires an odd number of teams."))

        ranking_order = {team.id: index for index, team in enumerate(self.teams)}
        candidates = sorted(teams, key=lambda team: ranking_order.get(team.id, -1), reverse=True)
        best_team = None
        best_cost = None

        for team in candidates:
            remaining = [candidate for candidate in teams if candidate.id != team.id]
            try:
                _, total_cost = self._compute_matching(remaining, bracket=bracket)
            except DrawUserError:
                continue
            if best_cost is None or total_cost < best_cost:
                best_team = team
                best_cost = total_cost

        if best_team is None:
            raise DrawUserError(_("Couldn't find a valid unmatched team for bye selection."))
        return best_team

    def generate_pairings(self, brackets):
        """Creates an undirected weighted graph for each bracket and gets the minimum weight matching"""
        from .pairing import Pairing
        pairings = OrderedDict()
        i = 0
        for j, (points, teams) in enumerate(brackets.items()):
            pairings[points] = []
            matching, _ = self._compute_matching(teams, bracket=j)
            for pairing in sorted(matching, key=lambda p: self.room_rank_ordering(p)):
                i += 1
                pairings[points].append(Pairing(teams=pairing, bracket=self.get_bracket(pairing, points), room_rank=i))

        return pairings

    def room_rank_ordering(self, p):
        return 0

    def get_bracket(self, pairing, points):
        return points


class GraphAllocatedSidesMixin(GraphGeneratorMixin):
    """Use Hungarian algorithm rather than Bloom.

    This is possible as assigning the sides creates a bipartite graph rather than
    a more complete graph."""

    def assignment_cost(self, t1, t2, size, bracket=None):
        penalty = super().assignment_cost(t1, t2, size, bracket)
        if penalty is None:
            return munkres.DISALLOWED
        return penalty

    def _compute_bipartite_matching(self, pool):
        aff_pool = list(pool[DebateSide.AFF])
        neg_pool = list(pool[DebateSide.NEG])
        aff_count = len(aff_pool)
        neg_count = len(neg_pool)

        if aff_count == 0 and neg_count == 0:
            return [], 0
        if aff_count != neg_count:
            raise DrawUserError(_("Saved side allocations left %(aff)d affirmative teams but %(neg)d negative teams in the bracket after pullups.") % {
                "aff": aff_count,
                "neg": neg_count,
            })

        n_teams = aff_count + neg_count
        matrix = [[self.assignment_cost(aff, neg, n_teams) for neg in neg_pool] for aff in aff_pool]
        matching = munkres.Munkres().compute(matrix)

        total_cost = 0
        for i_aff, i_neg in matching:
            cost = matrix[i_aff][i_neg]
            if cost == munkres.DISALLOWED:
                raise DrawUserError(_("Couldn't find a complete side-constrained matching for bye selection."))
            total_cost += cost

        return matching, total_cost

    def get_unmatched_team(self, pool):
        total_teams = len(pool[DebateSide.AFF]) + len(pool[DebateSide.NEG])
        if total_teams % 2 == 0:
            raise DrawUserError(_("Unmatched-team bye selection requires an odd number of teams."))

        ranking_order = {team.id: index for index, team in enumerate(self.teams)}
        candidates = sorted(
            list(pool[DebateSide.AFF]) + list(pool[DebateSide.NEG]),
            key=lambda team: ranking_order.get(team.id, -1),
            reverse=True,
        )
        best_team = None
        best_cost = None

        for team in candidates:
            remaining = {
                DebateSide.AFF: list(pool[DebateSide.AFF]),
                DebateSide.NEG: list(pool[DebateSide.NEG]),
            }
            remaining[team.allocated_side].remove(team)

            try:
                _, total_cost = self._compute_bipartite_matching(remaining)
            except DrawUserError:
                continue

            if best_cost is None or total_cost < best_cost:
                best_team = team
                best_cost = total_cost

        if best_team is None:
            raise DrawUserError(_("Couldn't find a valid unmatched team for bye selection."))
        return best_team

    def generate_pairings(self, brackets):
        from .pairing import Pairing
        pairings = OrderedDict()
        i = 0
        for points, pool in brackets.items():
            pairings[points] = []
            if len(pool[DebateSide.AFF]) == 0 and len(pool[DebateSide.NEG]) == 0:
                continue
            try:
                matching, _ = self._compute_bipartite_matching(pool)
            except DrawUserError as exc:
                raise DrawUserError(_("Saved side allocations left an invalid bracket %(bracket)s after pullups: %(message)s") % {
                    "bracket": points,
                    "message": exc,
                }) from exc

            for i_aff, i_neg in matching:
                i += 1
                pairings[points].append(Pairing(teams=[pool[DebateSide.AFF][i_aff], pool[DebateSide.NEG][i_neg]], bracket=points, room_rank=i))

        return pairings
