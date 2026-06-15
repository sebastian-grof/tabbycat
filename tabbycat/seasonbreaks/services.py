from collections import defaultdict
from dataclasses import dataclass
from math import floor

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

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


def prune_unused_break_identities(
        season: BreakSeason, team_ids=None, speaker_ids=None, adjudicator_ids=None) -> dict:
    """Delete candidate season identities that no longer point at any frozen or linked data."""
    deleted = {'teams': 0, 'speakers': 0, 'adjudicators': 0}

    team_ids = set(team_ids or [])
    if team_ids:
        unused_teams = BreakTeam.objects.filter(season=season, id__in=team_ids).annotate(
            link_count=Count('links', distinct=True),
            result_count=Count('tournament_results', distinct=True),
            participation_count=Count('speaker_participations', distinct=True),
        ).filter(link_count=0, result_count=0, participation_count=0)
        deleted['teams'] = unused_teams.count()
        unused_teams.delete()

    speaker_ids = set(speaker_ids or [])
    if speaker_ids:
        unused_speakers = BreakSpeaker.objects.filter(season=season, id__in=speaker_ids).annotate(
            link_count=Count('links', distinct=True),
            participation_count=Count('tournament_participations', distinct=True),
        ).filter(link_count=0, participation_count=0)
        deleted['speakers'] = unused_speakers.count()
        unused_speakers.delete()

    adjudicator_ids = set(adjudicator_ids or [])
    if adjudicator_ids:
        unused_adjudicators = BreakAdjudicator.objects.filter(season=season, id__in=adjudicator_ids).annotate(
            link_count=Count('links', distinct=True),
            stats_count=Count('tournament_stats', distinct=True),
        ).filter(link_count=0, stats_count=0)
        deleted['adjudicators'] = unused_adjudicators.count()
        unused_adjudicators.delete()

    return deleted


def prune_all_unused_break_identities(season: BreakSeason) -> dict:
    return prune_unused_break_identities(
        season,
        team_ids=BreakTeam.objects.filter(season=season).values_list('id', flat=True),
        speaker_ids=BreakSpeaker.objects.filter(season=season).values_list('id', flat=True),
        adjudicator_ids=BreakAdjudicator.objects.filter(season=season).values_list('id', flat=True),
    )


@transaction.atomic
def reassign_break_team_link(link: BreakTeamLink, new_break_team: BreakTeam) -> None:
    """Repoint a team link and carry its frozen stats to the new identity.

    Reassigning only the link leaves the tournament's frozen results and speaker
    participations attached to the old identity, so the old identity lingers in
    the rankings as a duplicate and its wins/ballots never merge into the new
    one. Move those rows (scoped to this link's tournament) too, then prune the
    old identity if nothing else references it.
    """
    old = link.break_team
    if old.id == new_break_team.id:
        return
    tournament = link.team.tournament

    results = BreakTeamTournamentResult.objects.filter(
        break_team=old,
        break_tournament__season=link.season,
        break_tournament__tournament=tournament,
    )
    for result in results:
        existing = BreakTeamTournamentResult.objects.filter(
            break_tournament=result.break_tournament, break_team=new_break_team,
        ).first()
        if existing is None:
            result.break_team = new_break_team
            result.save(update_fields=['break_team'])
        else:
            existing.wins += result.wins
            existing.ballots += result.ballots
            existing.speaker_score += result.speaker_score
            existing.rounds_debated += result.rounds_debated
            existing.majority_debated = existing.majority_debated or result.majority_debated
            existing.save()
            result.delete()

    participations = BreakSpeakerTournamentParticipation.objects.filter(
        break_team=old,
        break_tournament__season=link.season,
        break_tournament__tournament=tournament,
    )
    for participation in participations:
        existing = BreakSpeakerTournamentParticipation.objects.filter(
            break_tournament=participation.break_tournament,
            break_speaker=participation.break_speaker,
            break_team=new_break_team,
        ).first()
        if existing is None:
            participation.break_team = new_break_team
            participation.save(update_fields=['break_team'])
        else:
            existing.speeches += participation.speeches
            existing.rounds += participation.rounds
            existing.save(update_fields=['speeches', 'rounds'])
            participation.delete()

    link.break_team = new_break_team
    link.save(update_fields=['break_team'])
    prune_unused_break_identities(link.season, team_ids=[old.id])


@transaction.atomic
def reassign_break_speaker_link(link: BreakSpeakerLink, new_break_speaker: BreakSpeaker) -> None:
    """Repoint a speaker link and carry its frozen participations across."""
    old = link.break_speaker
    if old.id == new_break_speaker.id:
        return
    tournament = link.speaker.team.tournament if link.speaker.team else None

    participations = BreakSpeakerTournamentParticipation.objects.filter(
        break_speaker=old,
        break_tournament__season=link.season,
        break_tournament__tournament=tournament,
    )
    for participation in participations:
        existing = BreakSpeakerTournamentParticipation.objects.filter(
            break_tournament=participation.break_tournament,
            break_speaker=new_break_speaker,
            break_team=participation.break_team,
        ).first()
        if existing is None:
            participation.break_speaker = new_break_speaker
            participation.save(update_fields=['break_speaker'])
        else:
            existing.speeches += participation.speeches
            existing.rounds += participation.rounds
            existing.save(update_fields=['speeches', 'rounds'])
            participation.delete()

    link.break_speaker = new_break_speaker
    link.save(update_fields=['break_speaker'])
    prune_unused_break_identities(link.season, speaker_ids=[old.id])


@transaction.atomic
def reassign_break_adjudicator_link(link: BreakAdjudicatorLink, new_break_adjudicator: BreakAdjudicator) -> None:
    """Repoint an adjudicator link and carry its frozen stats across."""
    old = link.break_adjudicator
    if old.id == new_break_adjudicator.id:
        return
    tournament = link.adjudicator.tournament

    stats = BreakAdjudicatorTournamentStats.objects.filter(
        break_adjudicator=old,
        break_tournament__season=link.season,
        break_tournament__tournament=tournament,
    )
    for stat in stats:
        existing = BreakAdjudicatorTournamentStats.objects.filter(
            break_tournament=stat.break_tournament, break_adjudicator=new_break_adjudicator,
        ).first()
        if existing is None:
            stat.break_adjudicator = new_break_adjudicator
            stat.save(update_fields=['break_adjudicator'])
        else:
            existing.chair_count += stat.chair_count
            existing.panellist_count += stat.panellist_count
            existing.trainee_count += stat.trainee_count
            existing.total_count += stat.total_count
            existing.save()
            stat.delete()

    link.break_adjudicator = new_break_adjudicator
    link.save(update_fields=['break_adjudicator'])
    prune_unused_break_identities(link.season, adjudicator_ids=[old.id])


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
        team_identity_ids = list(BreakTeamLink.objects.filter(
            season=season, team__tournament=tournament,
        ).values_list('break_team_id', flat=True).distinct())
        speaker_identity_ids = list(BreakSpeakerLink.objects.filter(
            season=season, speaker__team__tournament=tournament,
        ).values_list('break_speaker_id', flat=True).distinct())
        BreakTeamLink.objects.filter(season=season, team__tournament=tournament).delete()
        BreakSpeakerLink.objects.filter(season=season, speaker__team__tournament=tournament).delete()
        prune_unused_break_identities(
            season, team_ids=team_identity_ids, speaker_ids=speaker_identity_ids,
        )

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


def _team_eligible_speakers(team: BreakTeam, region: BreakRegion) -> list[str]:
    participations = BreakSpeakerTournamentParticipation.objects.filter(
        break_team=team,
        break_tournament__region=region,
        break_tournament__counts_for_break=True,
        rounds__gte=2,
    ).values('break_speaker_id', 'break_speaker__name', 'break_tournament_id').distinct()
    speakers = {}
    for row in participations:
        speaker = speakers.setdefault(row['break_speaker_id'], {
            'name': row['break_speaker__name'],
            'tournaments': set(),
        })
        speaker['tournaments'].add(row['break_tournament_id'])
    return sorted(
        speaker['name'] for speaker in speakers.values()
        if len(speaker['tournaments']) >= 2
    )


def calculate_rankings(season: BreakSeason) -> dict[int, list[dict]]:
    quotas = {quota.region.id: quota.allocated for quota in calculate_region_quotas(season)}
    rankings = {}

    for region in season.regions.all():
        # N is the number of tournaments the region is expected to run this
        # season (set per region). Falling back to the count of counting
        # tournaments already added keeps the old behaviour for regions that
        # leave it at 0. Using the expected N lets the best N-1 rule produce a
        # meaningful live ranking before every tournament has been frozen.
        expected_tournaments = region.expected_tournaments or BreakTournament.objects.filter(
            season=season, region=region, counts_for_break=True,
        ).count()
        required_tournaments = max(expected_tournaments - 1, 0)
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
            eligible_speakers = _team_eligible_speakers(team, region)
            eligible_members = len(eligible_speakers)
            eligible = len(all_results) >= required_tournaments and eligible_members >= 2
            total_wins = sum(r.wins for r in counted)
            total_ballots = sum(r.ballots for r in counted)
            total_speaker_score = sum(r.speaker_score for r in counted)
            rows.append({
                'team': team,
                'eligible': eligible,
                'eligible_members': eligible_members,
                'eligible_speakers': eligible_speakers,
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

        # Rank purely by performance (wins > ballots > speaker score). Eligibility
        # only decides who can advance, not where a team sits in the standings, so
        # a stronger ineligible team still ranks above a weaker eligible one.
        rows.sort(key=lambda row: (row['wins'], row['ballots'], row['speaker_score']), reverse=True)
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


def _public_row(row, region, rank):
    return {
        'rank': rank,
        'team': row['team'].name,
        'team_id': row['team'].id,
        'region': region.name,
        'region_id': region.id,
        'wins': float(row['wins']),
        'ballots': float(row['ballots']),
        'speaker_score': float(row['speaker_score']),
        'participations': row['participations'],
    }


def _global_ranking_rows(rankings: dict[int, list[dict]], regions) -> list[dict]:
    """Flatten per-region rankings into one re-ranked global list.

    Fresh row dicts are built per region so re-ranking here never mutates the
    region-local ranks stored alongside them in the snapshot.
    """
    rows = []
    for region in regions:
        for rank, row in enumerate(rankings.get(region.id, []), start=1):
            rows.append(_public_row(row, region, rank))
    rows.sort(key=lambda row: (-row['wins'], -row['ballots'], -row['speaker_score'], row['team']))
    for rank, row in enumerate(rows, start=1):
        row['rank'] = rank
    return rows


def calculate_global_ranking(season: BreakSeason, regions=None) -> list[dict]:
    """Live global ranking across regions, mirroring the published snapshot.

    Admins can preview this without publishing a snapshot. Defaults to the
    publicly visible regions so it matches what the public page would show.
    """
    if regions is None:
        regions = list(season.regions.filter(public_visible=True))
    return _global_ranking_rows(calculate_rankings(season), regions)


def build_public_breaks_snapshot(season: BreakSeason, published_at=None) -> dict:
    """Serialize the current break state into a stable public snapshot."""
    published_at = published_at or timezone.now()
    quotas = {quota.region.id: quota for quota in calculate_region_quotas(season)}
    rankings = calculate_rankings(season)
    public_regions = list(season.regions.filter(public_visible=True))
    regions = []

    for region in public_regions:
        quota = quotas.get(region.id)
        region_rows = [
            _public_row(row, region, rank)
            for rank, row in enumerate(rankings.get(region.id, []), start=1)
        ]
        regions.append({
            'id': region.id,
            'name': region.name,
            'seq': region.seq,
            'public_visible': region.public_visible,
            'slots': quota.allocated if quota else 0,
            'participations': quota.participations if quota else 0,
            'ranking': region_rows,
        })

    global_rows = _global_ranking_rows(rankings, public_regions)

    return {
        'version': 1,
        'published_at': published_at.isoformat(),
        'show_global_ranking': season.public_global_ranking,
        'season': {
            'id': season.id,
            'name': season.name,
            'slug': season.slug,
            'league': season.league.name,
            'league_slug': season.league.slug,
            'league_display': season.get_league_display(),
            'regional_slots': season.regional_slots,
            'invited_teams': season.invited_teams,
            'effective_regional_slots': season.effective_regional_slots,
        },
        'regions': regions,
        'global_ranking': global_rows,
    }


def publish_public_breaks_snapshot(season: BreakSeason) -> dict:
    published_at = timezone.now()
    snapshot = build_public_breaks_snapshot(season, published_at=published_at)
    season.public_snapshot = snapshot
    season.public_published_at = published_at
    season.save(update_fields=['public_snapshot', 'public_published_at'])
    return snapshot


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
