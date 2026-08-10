from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from draw.models import DebateTeam
from draw.types import DebateSide

from .bye_scores import bye_average_results_enabled, refresh_bye_ballots, refresh_forfeit_ballots
from .models import BallotSubmission


def _refresh_auto_ballots(tournament, *, trigger_debate_is_bye):
    if bye_average_results_enabled(tournament) and not trigger_debate_is_bye:
        refresh_bye_ballots(tournament)

    if tournament.pref('teams_in_debate') == 2:
        refresh_forfeit_ballots(tournament)


@receiver(post_save, sender=BallotSubmission)
def refresh_byes_after_ballot_save(sender, instance, raw=False, **kwargs):
    if raw:  # fixture loading; related rows may not exist yet
        return
    tournament = instance.debate.round.tournament
    _refresh_auto_ballots(tournament, trigger_debate_is_bye=instance.debate.is_bye)


@receiver(post_delete, sender=BallotSubmission)
def refresh_byes_after_ballot_delete(sender, instance, **kwargs):
    tournament = instance.debate.round.tournament
    _refresh_auto_ballots(tournament, trigger_debate_is_bye=instance.debate.is_bye)


def _debate_might_need_bye_refresh(debate, debateteam_side=None):
    if debate.round.tournament.pref('teams_in_debate') != 2:
        return False

    if debateteam_side == DebateSide.BYE:
        return True

    if debate.debateteam_set.filter(side=DebateSide.BYE).exists():
        return True

    return debate.ballotsubmission_set.filter(
        submitter_type=BallotSubmission.Submitter.AUTOMATION,
        confirmed=True,
    ).exists()


@receiver(post_save, sender=DebateTeam)
def refresh_byes_after_debateteam_save(sender, instance, raw=False, **kwargs):
    if raw:  # fixture loading; related rows may not exist yet
        return
    if not _debate_might_need_bye_refresh(instance.debate, instance.side):
        return
    refresh_bye_ballots(instance.debate.round.tournament, debates=[instance.debate])


@receiver(post_delete, sender=DebateTeam)
def refresh_byes_after_debateteam_delete(sender, instance, **kwargs):
    if not _debate_might_need_bye_refresh(instance.debate, instance.side):
        return
    refresh_bye_ballots(instance.debate.round.tournament, debates=[instance.debate])
