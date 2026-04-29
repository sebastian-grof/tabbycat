from collections import defaultdict
from dataclasses import dataclass
from math import floor

from django.db import transaction

from adjallocation.models import DebateAdjudicator
from draw.types import DebateSide
from participants.models import Adjudicator, Speaker, Team
from results.models import BallotSubmission, SpeakerScore, TeamScore
from tournaments.models import Round

from .models import (
    BreakAdjudicator,
    BreakAdjudicatorLink,
    BreakAdjudicatorTournamentStats,
    BreakRegion,
    BreakSeason,
    BreakSpeaker,
    BreakSpeakerLink,
    BreakSpeakerTournamentParticipation,
    BreakTeam,
    BreakTeamLink,
    BreakTeamTournamentResult,
    BreakTournament,
)


def _unique_name(model, season, base_name):
    base_name = base_name or "Unnamed"
    if not model.objects.filter(season=season, name=base_name).exists():
        return base_name
    suffix = 2
    while model.objects.filter(season=season, name=f"{base_name} ({suffix})").exists():
        suffix += 1
    return f"{base_name} ({suffix})"


def _find_person_by_email(model, season, email):
    if not email:
        return None
    return model.objects.filter(season=season, email__iexact=email).first()


def get_or_create_break_team(season: BreakSeason, team: Team, fallback_region=None) -> BreakTeam:
    link = BreakTeamLink.objects.filter(season=season, team=team).select_related('break_team').first()
    if link is not None:
        return link.break_team

    name = team.short_name or team.long_name or str(team)
    matching_name = BreakTeam.objects.filter(season=season, name=name)
    break_team = matching_name.filter(institution=team.institution).first()
    if break_team is None and not matching_name.exists():
        identity_name = name
    elif break_team is None and team.institution is not None:
        identity_name = f"{name} ({team.institution.code})"
    else:
        identity_name = name
    if break_team is None:
        break_team = BreakTeam.objects.create(
            season=season,
            name=_unique_name(BreakTeam, season, identity_name),
            institution=team.institution,
            region=fallback_region,
        )
    elif break_team.region is None and fallback_region is not None:
        break_team.region = fallback_region
        break_team.save(update_fields=['region'])

    BreakTeamLink.objects.create(season=season, break_team=break_team, team=team)
    return break_team


def get_or_create_break_speaker(season: BreakSeason, speaker: Speaker) -> BreakSpeaker:
    link = BreakSpeakerLink.objects.filter(season=season, speaker=speaker).select_related('break_speaker').first()
    if link is not None:
        return link.break_speaker

    break_speaker = _find_person_by_email(BreakSpeaker, season, speaker.email)
    if break_speaker is None:
        break_speaker = BreakSpeaker.objects.create(
            season=season,
            name=speaker.name,
            email=speaker.email or None,
        )
    BreakSpeakerLink.objects.create(season=season, break_speaker=break_speaker, speaker=speaker)
    return break_speaker


def get_or_create_break_adjudicator(season: BreakSeason, adjudicator: Adjudicator) -> BreakAdjudicator:
    link = BreakAdjudicatorLink.objects.filter(
        season=season, adjudicator=adjudicator,
    ).select_related('break_adjudicator').first()
    if link is not None:
        return link.break_adjudicator

    break_adjudicator = _find_person_by_email(BreakAdjudicator, season, adjudicator.email)
    if break_adjudicator is None:
        break_adjudicator = BreakAdjudicator.objects.create(
            season=season,
            name=adjudicator.name,
            email=adjudicator.email or None,
            institution=adjudicator.institution,
        )
    BreakAdjudicatorLink.objects.create(season=season, break_adjudicator=break_adjudicator, adjudicator=adjudicator)
    return break_adjudicator


@transaction.atomic
def freeze_break_tournament(break_tournament: BreakTournament) -> dict:
    tournament = break_tournament.tournament
    season = break_tournament.season

    break_tournament.team_results.all().delete()
    break_tournament.speaker_participations.all().delete()
    break_tournament.adjudicator_stats.all().delete()

    prelim_rounds = list(tournament.round_set.filter(stage=Round.Stage.PRELIMINARY))
    prelim_round_count = len(prelim_rounds)

    team_totals = defaultdict(lambda: {
        'wins': 0.0,
        'ballots': 0.0,
        'speaker_score': 0.0,
        'real_debate_ids': set(),
    })

    speaker_totals = defaultdict(lambda: {'speeches': 0, 'round_ids': set()})

    if break_tournament.counts_for_break:
        team_scores = TeamScore.objects.filter(
            ballot_submission__confirmed=True,
            ballot_submission__discarded=False,
            debate_team__debate__round__tournament=tournament,
            debate_team__debate__round__stage=Round.Stage.PRELIMINARY,
        ).select_related('debate_team__team', 'debate_team__debate', 'ballot_submission')

        for team_score in team_scores:
            team = team_score.debate_team.team
            totals = team_totals[team]
            if team_score.win:
                totals['wins'] += 1
            if team_score.votes_given is not None and team_score.votes_possible:
                totals['ballots'] += (team_score.votes_given / team_score.votes_possible) * 3
            if team_score.score is not None:
                totals['speaker_score'] += team_score.score
            if team_score.debate_team.side != DebateSide.BYE:
                totals['real_debate_ids'].add(team_score.debate_team.debate_id)

        for team, totals in team_totals.items():
            break_team = get_or_create_break_team(season, team, break_tournament.region)
            rounds_debated = len(totals['real_debate_ids'])
            BreakTeamTournamentResult.objects.update_or_create(
                break_tournament=break_tournament,
                break_team=break_team,
                defaults={
                    'wins': totals['wins'],
                    'ballots': totals['ballots'],
                    'speaker_score': totals['speaker_score'],
                    'rounds_debated': rounds_debated,
                    'majority_debated': rounds_debated > (prelim_round_count / 2),
                },
            )

        speaker_scores = SpeakerScore.objects.filter(
            ballot_submission__confirmed=True,
            ballot_submission__discarded=False,
            debate_team__debate__round__tournament=tournament,
            debate_team__debate__round__stage=Round.Stage.PRELIMINARY,
        ).exclude(debate_team__side=DebateSide.BYE).select_related(
            'speaker', 'debate_team__team', 'debate_team__debate__round',
        )

        for speaker_score in speaker_scores:
            break_speaker = get_or_create_break_speaker(season, speaker_score.speaker)
            break_team = get_or_create_break_team(season, speaker_score.debate_team.team, break_tournament.region)
            key = (break_speaker, break_team)
            speaker_totals[key]['speeches'] += 1
            speaker_totals[key]['round_ids'].add(speaker_score.debate_team.debate.round_id)

        for (break_speaker, break_team), totals in speaker_totals.items():
            BreakSpeakerTournamentParticipation.objects.update_or_create(
                break_tournament=break_tournament,
                break_speaker=break_speaker,
                break_team=break_team,
                defaults={
                    'speeches': totals['speeches'],
                    'rounds': len(totals['round_ids']),
                },
            )

    else:
        BreakTeamLink.objects.filter(season=season, team__tournament=tournament).delete()
        BreakSpeakerLink.objects.filter(season=season, speaker__team__tournament=tournament).delete()

    confirmed_debate_ids = set(BallotSubmission.objects.filter(
        confirmed=True,
        discarded=False,
        debate__round__tournament=tournament,
        debate__round__stage=Round.Stage.PRELIMINARY,
    ).values_list('debate_id', flat=True))

    adjudicator_totals = defaultdict(lambda: {'chair': set(), 'panel': set(), 'trainee': set()})
    allocations = DebateAdjudicator.objects.filter(
        debate_id__in=confirmed_debate_ids,
    ).select_related('adjudicator', 'debate')

    for allocation in allocations:
        break_adjudicator = get_or_create_break_adjudicator(season, allocation.adjudicator)
        if allocation.type == DebateAdjudicator.TYPE_CHAIR:
            adjudicator_totals[break_adjudicator]['chair'].add(allocation.debate_id)
        elif allocation.type == DebateAdjudicator.TYPE_PANEL:
            adjudicator_totals[break_adjudicator]['panel'].add(allocation.debate_id)
        elif allocation.type == DebateAdjudicator.TYPE_TRAINEE:
            adjudicator_totals[break_adjudicator]['trainee'].add(allocation.debate_id)

    for break_adjudicator, totals in adjudicator_totals.items():
        chair_count = len(totals['chair'])
        panellist_count = len(totals['panel'])
        trainee_count = len(totals['trainee'])
        BreakAdjudicatorTournamentStats.objects.update_or_create(
            break_tournament=break_tournament,
            break_adjudicator=break_adjudicator,
            defaults={
                'chair_count': chair_count,
                'panellist_count': panellist_count,
                'trainee_count': trainee_count,
                'total_count': chair_count + panellist_count,
            },
        )

    break_tournament.mark_frozen()
    return {
        'teams': len(team_totals),
        'speakers': len(speaker_totals),
        'adjudicators': len(adjudicator_totals),
    }


@dataclass
class RegionQuota:
    region: BreakRegion
    participations: int
    raw_quota: float
    floor_quota: int
    remainder: float
    allocated: int


def calculate_region_quotas(season: BreakSeason) -> list[RegionQuota]:
    regions = list(season.regions.all())
    participation_by_region = {region.id: 0 for region in regions}

    results = BreakTeamTournamentResult.objects.filter(
        break_tournament__season=season,
        break_tournament__counts_for_break=True,
        majority_debated=True,
    ).select_related('break_tournament__region')
    for result in results:
        participation_by_region[result.break_tournament.region_id] += 1

    total_participations = sum(participation_by_region.values())
    total_slots = season.effective_regional_slots
    if total_participations == 0 or total_slots == 0:
        return [RegionQuota(region, participation_by_region.get(region.id, 0), 0, 0, 0, 0) for region in regions]

    quota = total_participations / total_slots
    rows = []
    allocated = 0
    for region in regions:
        participations = participation_by_region.get(region.id, 0)
        raw = participations / quota if quota else 0
        base = floor(raw)
        allocated += base
        rows.append(RegionQuota(region, participations, raw, base, raw - base, base))

    remaining = total_slots - allocated
    for row in sorted(rows, key=lambda r: (-r.remainder, r.region.seq, r.region.name))[:remaining]:
        row.allocated += 1
    return rows


def _team_member_eligibility(team: BreakTeam, region: BreakRegion) -> int:
    participations = BreakSpeakerTournamentParticipation.objects.filter(
        break_team=team,
        break_tournament__region=region,
        break_tournament__counts_for_break=True,
        rounds__gte=2,
    ).values('break_speaker_id', 'break_tournament_id').distinct()
    tournaments_by_speaker = defaultdict(set)
    for row in participations:
        tournaments_by_speaker[row['break_speaker_id']].add(row['break_tournament_id'])
    return sum(1 for tournaments in tournaments_by_speaker.values() if len(tournaments) >= 2)


def calculate_rankings(season: BreakSeason) -> dict[int, list[dict]]:
    quotas = {quota.region.id: quota.allocated for quota in calculate_region_quotas(season)}
    rankings = {}

    for region in season.regions.all():
        tournaments_in_region = BreakTournament.objects.filter(
            season=season, region=region, counts_for_break=True,
        ).count()
        required_tournaments = max(tournaments_in_region - 1, 0)
        result_limit = required_tournaments if required_tournaments else None

        team_ids = BreakTeamTournamentResult.objects.filter(
            break_tournament__season=season,
            break_tournament__region=region,
            break_tournament__counts_for_break=True,
        ).values_list('break_team_id', flat=True).distinct()

        rows = []
        for team in BreakTeam.objects.filter(id__in=team_ids).prefetch_related('tournament_results'):
            all_results = list(team.tournament_results.filter(
                break_tournament__season=season,
                break_tournament__region=region,
                break_tournament__counts_for_break=True,
                majority_debated=True,
            ).select_related('break_tournament'))
            strongest = sorted(all_results, key=lambda r: (r.wins, r.ballots, r.speaker_score), reverse=True)
            counted = strongest[:result_limit] if result_limit is not None else strongest
            eligible_members = _team_member_eligibility(team, region)
            eligible = len(all_results) >= required_tournaments and eligible_members >= 2
            total_wins = sum(r.wins for r in counted)
            total_ballots = sum(r.ballots for r in counted)
            total_speaker_score = sum(r.speaker_score for r in counted)
            rows.append({
                'team': team,
                'eligible': eligible,
                'eligible_members': eligible_members,
                'participations': len(all_results),
                'required_tournaments': required_tournaments,
                'counted_results': counted,
                'wins': total_wins,
                'ballots': total_ballots,
                'speaker_score': total_speaker_score,
                'advancing': False,
                'tie_at_cutoff': False,
                'ineligible_reasons': _ineligible_reasons(len(all_results), required_tournaments, eligible_members),
            })

        rows.sort(key=lambda row: (row['eligible'], row['wins'], row['ballots'], row['speaker_score']), reverse=True)
        seats = quotas.get(region.id, 0)
        eligible_rows = [row for row in rows if row['eligible']]
        cutoff_tuple = None
        if seats and len(eligible_rows) >= seats:
            cutoff = eligible_rows[seats - 1]
            cutoff_tuple = (cutoff['wins'], cutoff['ballots'], cutoff['speaker_score'])

        for index, row in enumerate(eligible_rows):
            if index < seats:
                row['advancing'] = True
            if cutoff_tuple and (row['wins'], row['ballots'], row['speaker_score']) == cutoff_tuple:
                row['tie_at_cutoff'] = True

        rankings[region.id] = rows
    return rankings


def _ineligible_reasons(participations, required_tournaments, eligible_members):
    reasons = []
    if participations < required_tournaments:
        reasons.append("not enough tournament participations")
    if eligible_members < 2:
        reasons.append("fewer than two eligible team members")
    return reasons


def season_summary(season: BreakSeason) -> dict:
    return {
        'regions': season.regions.count(),
        'tournaments': season.break_tournaments.count(),
        'league_tournaments': season.break_tournaments.filter(counts_for_break=True).count(),
        'nonleague_tournaments': season.break_tournaments.filter(counts_for_break=False).count(),
        'frozen_tournaments': season.break_tournaments.filter(frozen_at__isnull=False).count(),
        'teams': season.teams.count(),
        'speakers': season.speakers.count(),
        'adjudicators': season.adjudicators.count(),
    }
