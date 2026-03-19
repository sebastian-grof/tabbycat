from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from draw.models import DebateTeam
from draw.types import DebateSide
from tournaments.models import Tournament

from .bye_scores import bye_average_results_enabled, refresh_bye_ballots, refresh_forfeit_ballots
from .models import BallotSubmission, CrossExamination, ScoreCriterion

COMMON_CRITERIA = [
    "Strat\u00e9gia",
    "Organiz\u00e1cia",
    "Anal\u00fdza",
    "Prezent\u00e1cia",
]
SUBSTANTIVE_CRITERIA = [*COMMON_CRITERIA[:-1], "D\u00f4kazy", COMMON_CRITERIA[-1]]

DEFAULT_CROSS_EXAMINATIONS = [
    (1, "N3xS1"),
    (2, "S3xN1"),
    (3, "N1xS2"),
    (4, "S2xN2"),
]


def _default_criteria_data():
    criteria = []

    for seq, name in enumerate(SUBSTANTIVE_CRITERIA, start=1):
        criteria.append((name, seq, ScoreCriterion.SpeechType.SUBSTANTIVE))

    for seq, name in enumerate(COMMON_CRITERIA, start=len(SUBSTANTIVE_CRITERIA) + 1):
        criteria.append((name, seq, ScoreCriterion.SpeechType.REPLY))

    return criteria


@receiver(post_save, sender=Tournament)
def create_default_score_criteria(sender, instance, created, **kwargs):
    if not created:
        return

    if not ScoreCriterion.objects.filter(tournament=instance).exists():
        ScoreCriterion.objects.bulk_create([
            ScoreCriterion(
                tournament=instance,
                name=name,
                seq=seq,
                weight=1.0,
                min_score=2,
                max_score=6,
                step=0.5,
                required=True,
                speech_type=speech_type,
            )
            for name, seq, speech_type in _default_criteria_data()
        ])

    if not CrossExamination.objects.filter(tournament=instance).exists():
        CrossExamination.objects.bulk_create([
            CrossExamination(
                tournament=instance,
                seq=seq,
                name=name,
                weight=1.0,
                min_score=2,
                max_score=6,
                step=0.5,
                required=True,
            )
            for seq, name in DEFAULT_CROSS_EXAMINATIONS
        ])


def _refresh_auto_ballots(tournament, *, trigger_debate_is_bye):
    if bye_average_results_enabled(tournament) and not trigger_debate_is_bye:
        refresh_bye_ballots(tournament)

    if tournament.pref('teams_in_debate') == 2:
        refresh_forfeit_ballots(tournament)


@receiver(post_save, sender=BallotSubmission)
def refresh_byes_after_ballot_save(sender, instance, **kwargs):
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
def refresh_byes_after_debateteam_save(sender, instance, **kwargs):
    if not _debate_might_need_bye_refresh(instance.debate, instance.side):
        return
    refresh_bye_ballots(instance.debate.round.tournament, debates=[instance.debate])


@receiver(post_delete, sender=DebateTeam)
def refresh_byes_after_debateteam_delete(sender, instance, **kwargs):
    if not _debate_might_need_bye_refresh(instance.debate, instance.side):
        return
    refresh_bye_ballots(instance.debate.round.tournament, debates=[instance.debate])
