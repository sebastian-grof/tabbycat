from __future__ import annotations

import logging
from collections import defaultdict
from statistics import mean

from django.db import transaction

from draw.models import Debate, DebateTeam
from draw.types import DebateSide
from tournaments.models import Round

from .models import BallotSubmission, SpeakerScore, TeamScore

logger = logging.getLogger(__name__)

BYE_AVERAGE_MODE = 'average'
BYE_BALLOTS = 3


def bye_average_results_enabled(tournament):
    return (
        tournament.pref('teams_in_debate') == 2 and
        tournament.pref('bye_team_results') == BYE_AVERAGE_MODE
    )


def refresh_bye_ballots(tournament, debates=None):
    """Refreshes synthetic bye ballots for a tournament.

    This keeps bye scores aligned with the current confirmed, non-bye results so
    standings and future draws see the same running averages.
    """

    debates = list(debates) if debates is not None else None

    bye_debateteams = DebateTeam.objects.filter(
        debate__round__tournament=tournament,
        side=DebateSide.BYE,
    ).select_related('debate__round', 'team')

    stale_debates = []
    if debates is not None:
        debate_ids = [debate.id for debate in debates]
        bye_debateteams = bye_debateteams.filter(debate_id__in=debate_ids)
        stale_debates = [debate for debate in debates if not debate.debateteam_set.filter(side=DebateSide.BYE).exists()]

    bye_debateteams = list(bye_debateteams)
    if stale_debates:
        with transaction.atomic():
            for debate in stale_debates:
                _clear_auto_bye_ballot(debate)

    if not bye_debateteams:
        return

    mode = tournament.pref('bye_team_results')
    if mode == 'none':
        with transaction.atomic():
            for debateteam in bye_debateteams:
                _clear_bye_ballot(debateteam.debate)
        return

    if mode == 'points':
        with transaction.atomic():
            for debateteam in bye_debateteams:
                _sync_points_only_bye_ballot(debateteam)
        return

    if mode != BYE_AVERAGE_MODE:
        logger.warning("Unrecognised bye team results mode %s for %s", mode, tournament)
        return

    criteria = list(tournament.scorecriterion_set.order_by('seq'))
    crosses = list(tournament.crossexamination_set.order_by('seq'))
    using_replies = tournament.pref('reply_scores_enabled')
    reply_position = tournament.reply_position
    positions = list(tournament.positions)

    with transaction.atomic():
        for debateteam in bye_debateteams:
            refresh_single_bye_ballot(
                debateteam,
                criteria=criteria,
                crosses=crosses,
                positions=positions,
                reply_position=reply_position,
                using_replies=using_replies,
                uses_speaker_scores=_round_uses_speaker_scores(debateteam.debate.round, tournament),
            )


def refresh_single_bye_ballot(
    debateteam,
    *,
    criteria,
    crosses,
    positions,
    reply_position,
    using_replies,
    uses_speaker_scores,
):
    tournament = debateteam.debate.round.tournament
    ballotsub = _get_or_create_bye_ballot_submission(debateteam.debate)
    lineup = _existing_or_default_lineup(ballotsub, debateteam, positions, reply_position, using_replies)
    averages = _calculate_running_bye_averages(
        debateteam,
        criteria=criteria,
        crosses=crosses,
        positions=positions,
        reply_position=reply_position,
        using_replies=using_replies,
    )

    ballot_multiplier = _bye_score_multiplier(debateteam.debate.round, tournament)
    speaker_scores = {
        position: score if averages['speaker_raw_scores'].get(position) is not None else None
        for position, score in averages['speaker_raw_scores'].items()
    }
    team_total = averages['team_raw_total']

    ballotsub.crossexaminationscore_set.all().delete()
    ballotsub.crossexaminationscorebyadj_set.all().delete()
    ballotsub.teamscorebyadj_set.all().delete()
    ballotsub.speakerscorebyadj_set.all().delete()
    ballotsub.speakerscore_set.all().delete()

    TeamScore.objects.update_or_create(
        ballot_submission=ballotsub,
        debate_team=debateteam,
        defaults={
            'points': 1,
            'win': True,
            'margin': None,
            'score': team_total,
            'votes_given': BYE_BALLOTS,
            'votes_possible': BYE_BALLOTS,
            'has_ghost': False,
        },
    )

    _set_debate_result_status(debateteam.debate, Debate.STATUS_CONFIRMED)

    if not uses_speaker_scores:
        return ballotsub

    for position in positions:
        speaker = lineup.get(position)
        if speaker is None:
            logger.warning(
                "Couldn't assign a speaker for bye debate %s, team %s, position %s",
                debateteam.debate_id,
                debateteam.team_id,
                position,
            )
            continue

        raw_score = speaker_scores.get(position)
        if raw_score is None:
            normalized_default = _default_position_score(
                tournament,
                criteria,
                position,
                reply_position,
                using_replies,
            )
            raw_score = float(normalized_default) * ballot_multiplier

        SpeakerScore.objects.update_or_create(
            ballot_submission=ballotsub,
            debate_team=debateteam,
            position=position,
            defaults={
                'speaker': speaker,
                'rank': None,
                'score': raw_score,
                'ghost': False,
            },
        )

    return ballotsub


def _clear_bye_ballot(debate):
    debate.ballotsubmission_set.all().delete()
    _set_debate_result_status(debate, Debate.STATUS_NONE)


def _clear_auto_bye_ballot(debate):
    debate.ballotsubmission_set.filter(
        submitter_type=BallotSubmission.Submitter.AUTOMATION,
    ).delete()
    if not debate.ballotsubmission_set.exists():
        _set_debate_result_status(debate, Debate.STATUS_NONE)


def _sync_points_only_bye_ballot(debateteam):
    ballotsub = _get_or_create_bye_ballot_submission(debateteam.debate)
    ballotsub.speakerscore_set.all().delete()
    ballotsub.crossexaminationscore_set.all().delete()
    ballotsub.teamscorebyadj_set.all().delete()
    ballotsub.speakerscorebyadj_set.all().delete()
    ballotsub.crossexaminationscorebyadj_set.all().delete()

    TeamScore.objects.update_or_create(
        ballot_submission=ballotsub,
        debate_team=debateteam,
        defaults={
            'points': 1,
            'win': True,
            'margin': None,
            'score': None,
            'votes_given': None,
            'votes_possible': None,
            'has_ghost': False,
        },
    )
    _set_debate_result_status(debateteam.debate, Debate.STATUS_CONFIRMED)


def _get_or_create_bye_ballot_submission(debate):
    ballotsub = debate.ballotsubmission_set.filter(confirmed=True).order_by('-version').first()
    if ballotsub is None:
        ballotsub = BallotSubmission(
            submitter_type=BallotSubmission.Submitter.AUTOMATION,
            debate=debate,
            confirmed=True,
            discarded=False,
        )
        ballotsub.save()
        return ballotsub

    changed = False
    if ballotsub.submitter_type != BallotSubmission.Submitter.AUTOMATION:
        ballotsub.submitter_type = BallotSubmission.Submitter.AUTOMATION
        changed = True
    if ballotsub.discarded:
        ballotsub.discarded = False
        changed = True
    if not ballotsub.confirmed:
        ballotsub.confirmed = True
        changed = True
    if changed:
        ballotsub.save(update_fields=['submitter_type', 'discarded', 'confirmed'])
    return ballotsub


def _round_uses_speaker_scores(round, tournament):
    speakers_in_ballots = tournament.pref('speakers_in_ballots')
    if speakers_in_ballots == 'never':
        return False
    if speakers_in_ballots == 'prelim' and round.is_break_round:
        return False
    return True


def _bye_score_multiplier(round, tournament):
    if not _round_uses_speaker_scores(round, tournament):
        return 1.0
    if round.ballots_per_debate == 'per-adj' and tournament.pref('teams_in_debate') == 2:
        return float(BYE_BALLOTS)
    return 1.0


def _default_position_score(tournament, criteria, position, reply_position, using_replies):
    applicable = [
        criterion for criterion in criteria
        if criterion.applies_to_position(position, reply_position, using_replies)
    ]
    if applicable:
        return sum(_midpoint(criterion.min_score, criterion.max_score) * float(criterion.weight) for criterion in applicable)

    if using_replies and reply_position is not None and position == reply_position:
        return _midpoint(tournament.pref('reply_score_min'), tournament.pref('reply_score_max'))

    return _midpoint(tournament.pref('score_min'), tournament.pref('score_max'))


def _default_cross_total(tournament, crosses):
    if not tournament.pref('cross_examinations_enabled'):
        return 0.0
    if crosses:
        return sum(_midpoint(cross.min_score, cross.max_score) * float(cross.weight) for cross in crosses)
    return _midpoint(tournament.pref('cross_score_min'), tournament.pref('cross_score_max'))


def _midpoint(min_score, max_score):
    return (float(min_score) + float(max_score)) / 2.0


def _confirmed_real_speaker_scores(team, tournament):
    return SpeakerScore.objects.filter(
        debate_team__team=team,
        ballot_submission__confirmed=True,
        debate_team__debate__round__tournament=tournament,
        debate_team__debate__round__stage=Round.Stage.PRELIMINARY,
    ).exclude(
        debate_team__side=DebateSide.BYE,
    )


def _confirmed_real_team_scores(team, tournament):
    return TeamScore.objects.filter(
        debate_team__team=team,
        ballot_submission__confirmed=True,
        debate_team__debate__round__tournament=tournament,
        debate_team__debate__round__stage=Round.Stage.PRELIMINARY,
    ).exclude(
        debate_team__side=DebateSide.BYE,
    ).select_related('ballot_submission', 'debate_team__debate__round')


def _calculate_running_bye_averages(debateteam, *, criteria, crosses, positions, reply_position, using_replies):
    tournament = debateteam.debate.round.tournament
    speaker_scores = defaultdict(list)
    real_speaker_scores = _confirmed_real_speaker_scores(debateteam.team, tournament).filter(
        position__in=positions,
        ghost=False,
    ).values_list('position', 'score')
    for position, score in real_speaker_scores:
        speaker_scores[position].append(float(score))

    speaker_raw_scores = {}
    for position in positions:
        values = speaker_scores.get(position)
        if values:
            speaker_raw_scores[position] = mean(values)
        else:
            speaker_raw_scores[position] = _default_position_score(
                tournament,
                criteria,
                position,
                reply_position,
                using_replies,
            ) * _bye_score_multiplier(debateteam.debate.round, tournament)

    cross_scores = []
    if tournament.pref('cross_examinations_enabled'):
        teamscore_lookup = list(_confirmed_real_team_scores(debateteam.team, tournament))
        for teamscore in teamscore_lookup:
            if teamscore.score is None:
                continue
            speakers = SpeakerScore.objects.filter(
                ballot_submission=teamscore.ballot_submission,
                debate_team=teamscore.debate_team,
            )
            if not tournament.pref('teamscore_includes_ghosts'):
                speakers = speakers.filter(ghost=False)
            speech_total = sum(float(score) for score in speakers.values_list('score', flat=True))
            cross_scores.append(float(teamscore.score) - speech_total)

    if cross_scores:
        cross_raw_total = mean(cross_scores)
    else:
        cross_raw_total = _default_cross_total(tournament, crosses) * _bye_score_multiplier(debateteam.debate.round, tournament)

    team_raw_total = sum(float(score) for score in speaker_raw_scores.values()) + cross_raw_total

    return {
        'speaker_raw_scores': dict(speaker_raw_scores),
        'cross_raw_total': cross_raw_total,
        'team_raw_total': team_raw_total,
    }


def _existing_or_default_lineup(ballotsub, debateteam, positions, reply_position, using_replies):
    existing = {
        speaker_score.position: speaker_score.speaker
        for speaker_score in ballotsub.speakerscore_set.select_related('speaker')
    }
    if set(existing) >= set(positions):
        return existing

    lineup = dict(existing)
    fallback = _lineup_from_latest_real_debate(debateteam, positions, reply_position)
    roster = list(debateteam.team.speaker_set.order_by('id'))
    first_roster_speaker = roster[0] if roster else None

    for index, position in enumerate(positions, start=1):
        if position in lineup and lineup[position] is not None:
            continue

        speaker = fallback.get(position)
        if speaker is None and position != reply_position:
            roster_index = index - 1
            if roster_index < len(roster):
                speaker = roster[roster_index]
        if speaker is None and using_replies and reply_position is not None and position == reply_position:
            speaker = fallback.get(reply_position) or lineup.get(1) or first_roster_speaker
        if speaker is None:
            speaker = first_roster_speaker

        lineup[position] = speaker

    return lineup


def _lineup_from_latest_real_debate(debateteam, positions, reply_position):
    latest_scores = list(
        SpeakerScore.objects.filter(
            debate_team__team=debateteam.team,
            ballot_submission__confirmed=True,
            debate_team__debate__round__tournament=debateteam.debate.round.tournament,
            debate_team__debate__round__stage=Round.Stage.PRELIMINARY,
            debate_team__debate__round__seq__lt=debateteam.debate.round.seq,
        ).exclude(
            debate_team__side=DebateSide.BYE,
        ).select_related('speaker', 'ballot_submission__debate__round').order_by(
            '-ballot_submission__debate__round__seq',
            'position',
        )
    )
    if not latest_scores:
        return {}

    latest_round_seq = latest_scores[0].ballot_submission.debate.round.seq
    lineup = {}
    for score in latest_scores:
        if score.ballot_submission.debate.round.seq != latest_round_seq:
            break
        if score.position in positions:
            lineup[score.position] = score.speaker

    if reply_position is not None and reply_position in lineup:
        return lineup

    if reply_position is not None:
        lineup[reply_position] = next(iter(lineup.values()), None)

    return lineup


def _set_debate_result_status(debate, status):
    if debate.result_status != status:
        debate.result_status = status
        debate.save(update_fields=['result_status'])
