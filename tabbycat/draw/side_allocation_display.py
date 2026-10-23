"""Read-only team navigation metadata for the administrator's side editor."""

import logging

from django.utils.formats import localize
from django.utils.translation import gettext as _

from participants.models import Team
from results.models import TeamScore
from standings.base import StandingsError
from standings.teams import TeamStandingsGenerator

logger = logging.getLogger(__name__)


def get_team_navigation(tournament, selected_round, teams):
    navigation = {
        "available": False,
        "context": _("No prior results. Standings and bracket views use alphabetical order."),
        "teams": [{
            "id": team.id,
            "shortName": team.short_name,
            "longName": team.long_name,
            "rank": None,
            "bracketOrder": None,
            "bracketLabel": "",
            "statistics": {"wins": 0, "ballots": 0, "team_points": 0},
        } for team in teams],
    }
    if selected_round is None:
        return navigation

    previous_round = tournament.prelim_rounds().filter(seq__lt=selected_round.seq).order_by("-seq").first()
    # Passing round=None to the generator would include *all* results.
    if previous_round is None or not TeamScore.objects.filter(
        debate_team__team__tournament=tournament,
        debate_team__debate__round__stage=previous_round.Stage.PRELIMINARY,
        debate_team__debate__round__seq__lte=previous_round.seq,
        ballot_submission__confirmed=True,
    ).exists():
        return navigation

    navigation["context"] = _("Standings through %(round)s") % {"round": previous_round.name}
    metrics = tournament.pref("team_standings_precedence")
    if not metrics:
        navigation["context"] += ". " + _("No standings metrics configured; using alphabetical order.")

    for team in navigation["teams"]:
        team["statistics"] = {"wins": None, "ballots": None, "team_points": None}

    try:
        extra_metrics = [key for key in ("wins", "num_adjs", "speaks_sum") if key not in metrics]
        generator = TeamStandingsGenerator(metrics, ("rank",) if metrics else (), extra_metrics=extra_metrics, tiebreak="shortname")
        ranked_teams = tournament.team_set.filter(id__in=[team.id for team in teams]).exclude(type=Team.TYPE_BYE)
        standings = list(generator.generate(ranked_teams, round=previous_round))
    except StandingsError:
        logger.exception("Could not calculate side allocation display standings for round %s", selected_round.id)
        navigation["context"] += ". " + _("Standings unavailable; using alphabetical order.")
        return navigation

    by_id = {standing.instance_id: standing for standing in standings}
    for team in navigation["teams"]:
        standing = by_id.get(team["id"])
        if standing is None:
            continue
        team["statistics"] = {
            "wins": standing.metrics["wins"] or 0,
            "ballots": standing.metrics["num_adjs"] or 0,
            "team_points": standing.metrics["speaks_sum"] or 0,
        }

    if not metrics:
        return navigation

    primary_metric = generator.precedence[0]
    values = sorted({standing.metrics[primary_metric] or 0 for standing in standings}, reverse=True)
    bracket_orders = {value: index for index, value in enumerate(values)}
    metric_name = str(generator.metric_annotators[0].name).capitalize()
    for team in navigation["teams"]:
        standing = by_id.get(team["id"])
        if standing is None:
            continue
        value = standing.metrics[primary_metric] or 0
        team.update({
            "rank": standing.get_ranking("rank"),
            "bracketOrder": bracket_orders[value],
            "bracketLabel": _("%(metric)s: %(value)s") % {"metric": metric_name, "value": localize(value)},
        })
    navigation["available"] = True
    return navigation
