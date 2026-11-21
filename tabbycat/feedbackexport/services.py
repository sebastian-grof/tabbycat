import gzip
import hashlib
import json
import logging
import math
import random
import re
import urllib.error
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone, translation
from django.utils.text import slugify

from adjallocation.models import DebateAdjudicator
from adjfeedback.models import AdjudicatorFeedback
from results.models import BallotSubmission
from tournaments.models import Tournament

from .models import AdjudicatorStatsExportEvent, FeedbackExportEvent, ResultsExportEvent, SeasonBreaksExportEvent

logger = logging.getLogger(__name__)

SOURCE_SYSTEM = 'tabbycat-sda'
DEFAULT_TIMEOUT = 10
MAX_ATTEMPTS = 8
SEASON_LABEL_RE = re.compile(r'(20\d{2})\s*[/-]\s*(20\d{2})')
RESULTS_PAYLOAD_VERSION = 1
# The results contract asks for gzip above 1 MB (DR accepts up to 10 MB).
RESULTS_GZIP_THRESHOLD = 1024 * 1024
SEASON_BREAKS_PAYLOAD_VERSION = 1
SEASON_BREAKS_SNAPSHOT_VERSION = 1
# DR's limits for /api/v1/season-breaks/ (registry/api/ingest/season_breaks.py).
SEASON_BREAKS_MAX_REGIONS = 50
SEASON_BREAKS_MAX_BYTES = 2500 * 1024
SDA_SEASON_RE = re.compile(r'^\d{4}/\d{4}$')


def feedback_export_enabled():
    return bool(getattr(settings, 'FEEDBACK_EXPORT_ENABLED', False))


def feedback_export_endpoint():
    return getattr(settings, 'FEEDBACK_EXPORT_ENDPOINT', '')


def feedback_export_token():
    return getattr(settings, 'FEEDBACK_EXPORT_TOKEN', '')


def adjudicator_stats_export_enabled():
    return bool(getattr(settings, 'ADJUDICATOR_STATS_EXPORT_ENABLED', False))


def adjudicator_stats_export_endpoint():
    return getattr(settings, 'ADJUDICATOR_STATS_EXPORT_ENDPOINT', '')


def adjudicator_stats_export_token():
    return getattr(settings, 'ADJUDICATOR_STATS_EXPORT_TOKEN', '') or feedback_export_token()


def results_export_enabled():
    return bool(getattr(settings, 'RESULTS_EXPORT_ENABLED', False))


def results_export_endpoint():
    return getattr(settings, 'RESULTS_EXPORT_ENDPOINT', '')


def results_export_token():
    return getattr(settings, 'RESULTS_EXPORT_TOKEN', '') or feedback_export_token()


def season_breaks_export_enabled():
    return bool(getattr(settings, 'SEASON_BREAKS_EXPORT_ENABLED', False))


def season_breaks_export_endpoint():
    return getattr(settings, 'SEASON_BREAKS_EXPORT_ENDPOINT', '')


def season_breaks_export_token():
    # DR authorises season breaks with the results:write scope.
    return getattr(settings, 'SEASON_BREAKS_EXPORT_TOKEN', '') or results_export_token()


def make_idempotency_key(feedback_id, content_hash=None):
    base = '%s:feedback:%s' % (SOURCE_SYSTEM, feedback_id)
    if content_hash:
        return '%s:%s:v2' % (base, content_hash[:12])
    return '%s:v2' % base


def make_adjudicator_stats_idempotency_key(tournament, content_hash=None):
    base = '%s:adjudicator-activity:%s' % (SOURCE_SYSTEM, tournament.id)
    if content_hash:
        return '%s:%s:v2' % (base, content_hash[:12])
    return '%s:v2' % base


def normalise_json_value(value):
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [normalise_json_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): normalise_json_value(v) for k, v in value.items()}
    return value


def participant_institution_payload(institution):
    if not institution:
        return None
    return {
        'id': institution.id,
        'name': institution.name,
        'code': institution.code,
        'region': institution.region.name if institution.region else None,
    }


def adjudicator_payload(adjudicator, *, include_profile=False):
    payload = {
        'local_id': adjudicator.id,
        'name': adjudicator.name,
        'email': adjudicator.email,
        'institution': participant_institution_payload(adjudicator.institution),
    }
    return payload


def debate_adjudicator_role(debate_adjudicator):
    if not debate_adjudicator:
        return None
    return str(debate_adjudicator.get_type_display())


def source_payload(feedback):
    if feedback.source_team_id:
        debate_team = feedback.source_team
        team = debate_team.team
        return {
            'type': 'team',
            'local_id': team.id,
            'display_name': team.short_name,
        }

    debate_adjudicator = feedback.source_adjudicator
    if debate_adjudicator is None or debate_adjudicator.adjudicator is None:
        # A feedback must have exactly one source, but guard against a missing
        # relation so a single bad row can't crash payload building for the batch.
        return {'type': 'unknown', 'local_id': None, 'display_name': None}

    adjudicator = debate_adjudicator.adjudicator
    payload = {
        'type': 'adjudicator',
        'local_id': adjudicator.id,
        'display_name': adjudicator.name,
    }
    if adjudicator.email:
        payload['email'] = adjudicator.email
    return payload


def validate_feedback_payload(payload):
    """Assert the contract DR requires before we queue an event, so bad data
    surfaces as a clear local error instead of an opaque remote HTTP 4xx."""
    source = payload.get('source') or {}
    if not source.get('type'):
        raise ValueError('Feedback source has no type; cannot identify who gave the feedback.')
    if not (source.get('display_name') or '').strip():
        raise ValueError('Feedback source is missing a name (source type %r).' % source.get('type'))

    target = payload.get('target') or {}
    if not (target.get('name') or '').strip():
        raise ValueError('Feedback target adjudicator is missing a name.')
    return payload


def answer_type_payload(question):
    answer_type = question.answer_type
    mapping = {
        question.AnswerType.BOOLEAN_CHECKBOX: 'boolean',
        question.AnswerType.BOOLEAN_SELECT: 'boolean',
        question.AnswerType.INTEGER_TEXTBOX: 'integer',
        question.AnswerType.INTEGER_SCALE: 'integer',
        question.AnswerType.FLOAT: 'float',
        question.AnswerType.TEXT: 'text',
        question.AnswerType.LONGTEXT: 'text',
        question.AnswerType.SINGLE_SELECT: 'single_select',
        question.AnswerType.MULTIPLE_SELECT: 'multiple_select',
        question.AnswerType.DATETIME: 'datetime',
    }
    return mapping.get(answer_type, answer_type)


DR_ASSESSMENT_REFERENCES = {'assessment', 'posudok'}
DR_COMMENT_REFERENCES = {
    'assessment_comment',
    'comment',
    'comments',
    'komentar',
    'komentare',
    'komentare_k_rozhodnutiu',
    'komentare_rozhodca',
}


def question_reference_payload(question):
    reference = getattr(question, 'reference', None)
    if reference is not None:
        return reference
    try:
        return question.adjudicatorfeedbackquestion.reference
    except (AttributeError, ObjectDoesNotExist):
        return None


def question_search_text(question):
    return ' '.join(str(value or '') for value in (
        question_reference_payload(question),
        getattr(question, 'name', ''),
        getattr(question, 'text', ''),
    )).casefold()


def canonical_question_reference(feedback, question):
    reference = question_reference_payload(question)
    reference_key = str(reference or '').strip().casefold()
    search_text = question_search_text(question)

    if feedback.source_adjudicator_id:
        if reference_key in DR_COMMENT_REFERENCES or 'koment' in search_text or 'comment' in search_text:
            return 'assessment_comment'
        if reference_key in DR_ASSESSMENT_REFERENCES or 'posudok' in search_text or 'assessment' in search_text:
            return 'assessment'
    elif feedback.source_team_id:
        if reference_key in DR_COMMENT_REFERENCES or 'koment' in search_text or 'comment' in search_text:
            return 'comment'

    return reference


def unique_question_reference(reference, question, seen_references):
    if not reference:
        return reference

    reference = str(reference)
    if reference not in seen_references:
        seen_references.add(reference)
        return reference

    original_reference = question_reference_payload(question)
    candidates = []
    if original_reference and original_reference != reference:
        candidates.append(str(original_reference))
    candidates.extend([
        '%s_%s' % (reference, question.id),
        'question_%s' % question.id,
    ])
    for candidate in candidates:
        if candidate not in seen_references:
            seen_references.add(candidate)
            return candidate

    return ''


def answers_payload(feedback):
    answers = []
    seen_references = set()
    ordered_answers = getattr(feedback, 'export_answers', None)
    if ordered_answers is None:
        ordered_answers = feedback.answers.select_related('question', 'question__adjudicatorfeedbackquestion').order_by('question__seq', 'question__id')
    for answer in ordered_answers:
        question = answer.question
        try:
            value = answer.deserialize_answer()
        except Exception:
            logger.exception('Could not deserialize feedback answer %s', answer.id)
            value = answer.answer
        value = normalise_json_value(value)
        question_reference = canonical_question_reference(feedback, question)
        question_reference = unique_question_reference(question_reference, question, seen_references)
        answers.append({
            'question_reference': question_reference,
            'question_text': question.text,
            'answer_type': answer_type_payload(question),
            'raw_value': value,
            'value': value,
        })
    return answers


def timestamp_payload(value):
    return value.isoformat() if value else None


def season_catalog_label(season):
    if not season:
        return None
    for value in (season.name, season.slug):
        match = SEASON_LABEL_RE.search(value or '')
        if match:
            return '%s/%s' % match.groups()
    return season.name


def tournament_break_season(tournament):
    if hasattr(tournament, '_export_break_tournament'):
        return tournament._export_break_tournament
    try:
        return tournament.break_tournaments.select_related('season', 'season__league').order_by(
            '-season__active', '-season__created_at',
        ).first()
    except Exception:
        logger.exception('Could not resolve feedback export season for tournament %s', tournament.id)
        return None


def build_feedback_payload(feedback):
    feedback = load_feedback(feedback)
    debate = feedback.debate
    round_ = debate.round
    tournament = round_.tournament
    break_tournament = tournament_break_season(tournament)
    break_season = break_tournament.season if break_tournament else None
    debate_adjudicator = feedback.debate_adjudicator
    feedback_affects_scores = tournament.pref('feedback_affects_adjudicator_scores')

    return {
        'source_system': SOURCE_SYSTEM,
        'feedback_id': feedback.id,
        'idempotency_key': make_idempotency_key(feedback.id),
        'version': feedback.version,
        'created_at': timestamp_payload(feedback.timestamp),
        'updated_at': timestamp_payload(feedback.confirm_timestamp or feedback.timestamp),
        'confirmed_at': timestamp_payload(feedback.confirm_timestamp),
        'confirmed': feedback.confirmed,
        'ignored': feedback.ignored,
        'feedback_affects_adjudicator_scores': feedback_affects_scores,
        'score_ignored_in_tabbycat': not feedback_affects_scores,
        'score': feedback.score,
        'tournament': {
            'id': tournament.id,
            'slug': tournament.slug,
            'name': tournament.name,
            'short_name': tournament.short_name,
            'season': season_catalog_label(break_season),
            'league': break_season.league.name if break_season else None,
            'league_slug': break_season.league.slug if break_season else None,
        },
        'round': {
            'seq': round_.seq,
            'name': round_.name,
            'abbreviation': round_.abbreviation,
        },
        'debate': {
            'id': debate.id,
        },
        'target': {
            'judge_profile_id': None,
            'local_adjudicator_id': feedback.adjudicator_id,
            'name': feedback.adjudicator.name,
            'email': feedback.adjudicator.email,
            'role': debate_adjudicator_role(debate_adjudicator),
        },
        'source': source_payload(feedback),
        'answers': answers_payload(feedback),
    }


def load_tournament_for_activity(tournament):
    from seasonbreaks.models import BreakTournament

    if isinstance(tournament, BreakTournament):
        return Tournament.objects.get(pk=tournament.tournament_id)
    if isinstance(tournament, Tournament):
        return tournament
    return Tournament.objects.get(pk=tournament)


def break_tournament_metadata(tournament):
    break_tournament = tournament_break_season(tournament)
    if break_tournament is None:
        return None, None
    break_tournament = break_tournament.__class__.objects.select_related(
        'season', 'season__league', 'region', 'tournament',
    ).get(pk=break_tournament.pk)
    return break_tournament, break_tournament.season


def _adjudicator_activity_rows(tournament):
    confirmed_debate_ids = set(BallotSubmission.objects.filter(
        confirmed=True,
        discarded=False,
        debate__round__tournament=tournament,
    ).values_list('debate_id', flat=True))

    totals = {}
    allocations = DebateAdjudicator.objects.filter(
        debate_id__in=confirmed_debate_ids,
    ).select_related(
        'adjudicator',
    ).order_by('adjudicator__name', 'adjudicator_id')

    for allocation in allocations:
        adjudicator = allocation.adjudicator
        row = totals.setdefault(adjudicator.id, {
            'adjudicator': adjudicator,
            'chair': set(),
            'panel': set(),
            'trainee': set(),
        })
        if allocation.type == DebateAdjudicator.TYPE_CHAIR:
            row['chair'].add(allocation.debate_id)
        elif allocation.type == DebateAdjudicator.TYPE_PANEL:
            row['panel'].add(allocation.debate_id)
        elif allocation.type == DebateAdjudicator.TYPE_TRAINEE:
            row['trainee'].add(allocation.debate_id)

    adjudicators = []
    for row in sorted(totals.values(), key=lambda item: (item['adjudicator'].name, item['adjudicator'].id)):
        adjudicator = row['adjudicator']
        chair_count = len(row['chair'])
        panellist_count = len(row['panel'])
        trainee_count = len(row['trainee'])
        adjudicators.append({
            'judge_profile_id': None,
            'local_adjudicator_id': adjudicator.id,
            'name': adjudicator.name,
            'email': adjudicator.email,
            'chair_count': chair_count,
            'panellist_count': panellist_count,
            'trainee_count': trainee_count,
            'total_count': chair_count + panellist_count,
        })
    return adjudicators


def build_adjudicator_stats_payload(tournament, *, idempotency_key=None):
    tournament = load_tournament_for_activity(tournament)
    break_tournament, season = break_tournament_metadata(tournament)
    season_payload = None
    if season is not None:
        season_payload = {
            'id': season.id,
            'slug': season.slug,
            'name': season.name,
            'league': season.league.name,
            'league_slug': season.league.slug,
        }

    break_tournament_payload = None
    if break_tournament is not None:
        break_tournament_payload = {
            'id': break_tournament.id,
            'counts_for_break': break_tournament.counts_for_break,
            'frozen_at': timestamp_payload(break_tournament.frozen_at),
            'region': {
                'id': break_tournament.region_id,
                'name': break_tournament.region.name,
                'slug': slugify(break_tournament.region.name),
            } if break_tournament.region_id else None,
        }

    return {
        'source_system': SOURCE_SYSTEM,
        'idempotency_key': idempotency_key or make_adjudicator_stats_idempotency_key(tournament),
        'version': 2,
        'season': season_payload,
        'tournament': {
            'id': tournament.id,
            'slug': tournament.slug,
            'name': tournament.name,
            'short_name': tournament.short_name,
            'season': season_catalog_label(season),
            'league': season.league.name if season else None,
            'league_slug': season.league.slug if season else None,
        },
        'break_tournament': break_tournament_payload,
        'adjudicators': _adjudicator_activity_rows(tournament),
    }


def adjudicator_stats_content_hash(tournament):
    tournament = load_tournament_for_activity(tournament)
    content_payload = build_adjudicator_stats_payload(tournament, idempotency_key='')
    content_hash = payload_hash(content_payload)
    payload = content_payload
    payload['idempotency_key'] = make_adjudicator_stats_idempotency_key(tournament, content_hash)
    return payload_hash(payload)


def adjudicator_stats_event_needs_reexport(event, tournament=None):
    if event is None or event.status != AdjudicatorStatsExportEvent.Status.SENT:
        return False
    tournament = tournament or event.tournament
    if tournament is None:
        return False
    return event.payload_hash != adjudicator_stats_content_hash(tournament)


# ==============================================================================
# Tournament results snapshot (POST /api/v1/results/, contract v1)
# ==============================================================================
#
# Data minimisation: many debaters are minors, so the payload carries only the
# fields listed in the results contract. Never add phone, gender, pronoun,
# url_key, code names of people, private URLs or IP addresses here.

DEBATE_ROLE_NAMES = {
    DebateAdjudicator.TYPE_CHAIR: 'chair',
    DebateAdjudicator.TYPE_PANEL: 'panellist',
    DebateAdjudicator.TYPE_TRAINEE: 'trainee',
}
DEBATE_ROLE_ORDER = {'chair': 0, 'panellist': 1, 'trainee': 2}


def make_results_idempotency_key(tournament, content_hash):
    return '%s:results:%s:%s:v1' % (SOURCE_SYSTEM, tournament.id, content_hash[:12])


def results_content_hash(payload):
    """Hash of the results content only: the build time and the key derived
    from this hash are excluded, so an unchanged tournament keeps its key."""
    return payload_hash({k: v for k, v in payload.items() if k not in ('generated_at', 'idempotency_key')})


def _blank_to_none(value):
    return value if value not in ('', None) else None


def _number(value):
    """Standings metrics as JSON numbers; anything else (e.g. who-beat-whom's
    "n/a", NaN from a one-speech standard deviation) becomes null."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _side_name(tournament, side):
    from tournaments.utils import get_side_name
    name = str(get_side_name(tournament, side, 'full'))
    return name[:1].upper() + name[1:]


def _results_break_tournament_payload(break_tournament, season):
    if break_tournament is None:
        return None
    return {
        'id': break_tournament.id,
        'counts_for_break': break_tournament.counts_for_break,
        'frozen_at': timestamp_payload(break_tournament.frozen_at),
        'region': {
            'id': break_tournament.region_id,
            'name': break_tournament.region.name,
            'slug': slugify(break_tournament.region.name),
        } if break_tournament.region_id else None,
        'season': {
            'id': season.id,
            'slug': season.slug,
            'name': season.name,
        },
    }


def _results_tournament_payload(tournament, rounds, break_tournament, season):
    dates = sorted(timezone.localdate(r.starts_at) for r in rounds if r.starts_at)
    return {
        'id': tournament.id,
        'slug': tournament.slug,
        'name': tournament.name,
        'short_name': _blank_to_none(tournament.short_name),
        'season': season_catalog_label(season),
        'league': season.league.name if season else None,
        'league_slug': season.league.slug if season else None,
        'starts_on': dates[0].isoformat() if dates else None,
        'ends_on': dates[-1].isoformat() if dates else None,
        'format': {
            'teams_per_debate': tournament.pref('teams_in_debate'),
            'speakers_per_team': tournament.pref('substantive_speakers'),
            'reply_speeches': bool(tournament.pref('reply_scores_enabled')),
            'uses_cross_examination': bool(tournament.pref('cross_examinations_enabled')),
            # Metric keys in the configured order, so DR can lay out the tabs'
            # columns the way this tournament ranks them.
            'team_standings_precedence': [str(m) for m in tournament.pref('team_standings_precedence')],
            'team_standings_extra_metrics': [str(m) for m in tournament.pref('team_standings_extra_metrics')],
            'speaker_standings_precedence': [str(m) for m in tournament.pref('speaker_standings_precedence')],
            'speaker_standings_extra_metrics': [str(m) for m in tournament.pref('speaker_standings_extra_metrics')],
        },
        'break_tournament': _results_break_tournament_payload(break_tournament, season),
    }


def _season_team_links(tournament, season):
    from seasonbreaks.models import BreakTeamLink

    links = {}
    queryset = BreakTeamLink.objects.filter(team__tournament=tournament).select_related('break_team').order_by('-season_id', 'id')
    for link in queryset:
        # Prefer the season this tournament counts for; otherwise the newest season.
        if link.team_id not in links or (season is not None and link.season_id == season.id):
            links[link.team_id] = link
    return {team_id: {'id': link.break_team_id, 'name': link.break_team.name} for team_id, link in links.items()}


def _results_teams_payload(tournament, season):
    from participants.models import Speaker, Team

    season_teams = _season_team_links(tournament, season)
    teams = Team.objects.filter(tournament=tournament).prefetch_related(
        'break_categories',
        Prefetch('speaker_set', queryset=Speaker.objects.order_by('id').prefetch_related('categories')),
    ).order_by('id')
    payload = []
    for team in teams:
        payload.append({
            'id': team.id,
            'name': team.long_name,
            'short_name': _blank_to_none(team.short_name),
            'code_name': _blank_to_none(team.code_name),
            'institution_id': team.institution_id,
            'season_team': season_teams.get(team.id),
            'break_category_ids': sorted(category.id for category in team.break_categories.all()),
            'speakers': [{
                'id': speaker.id,
                'name': speaker.name,
                'email': _blank_to_none(speaker.email),
                'anonymous': speaker.anonymous,
                'speaker_category_ids': sorted(category.id for category in speaker.categories.all()),
            } for speaker in team.speaker_set.all()],
        })
    return payload, [team.institution_id for team in teams]


def _results_adjudicators_payload(tournament, panel_adjudicator_ids):
    from django.db.models import Q
    from participants.models import Adjudicator

    adjudicators = Adjudicator.objects.filter(
        Q(tournament=tournament) | Q(id__in=panel_adjudicator_ids),
    ).order_by('id')
    payload = [{
        'id': adjudicator.id,
        'name': adjudicator.name,
        'email': _blank_to_none(adjudicator.email),
        'institution_id': adjudicator.institution_id,
        'anonymous': adjudicator.anonymous,
        'trainee': adjudicator.trainee,
        'independent': adjudicator.independent,
        'adj_core': adjudicator.adj_core,
        # Same meaning as in the feedback payload; this fork keeps no DR mapping.
        'judge_profile_id': None,
    } for adjudicator in adjudicators]
    return payload, [adjudicator.institution_id for adjudicator in adjudicators]


def _results_institutions_payload(institution_ids):
    from participants.models import Institution

    institutions = Institution.objects.filter(id__in={i for i in institution_ids if i}).select_related('region').order_by('id')
    return [{
        'id': institution.id,
        'name': institution.name,
        'code': institution.code,
        'region': institution.region.name if institution.region_id else None,
    } for institution in institutions]


def _results_rounds_payload(tournament, rounds):
    from motions.models import RoundMotion
    from tournaments.models import Round

    motions = {}
    for round_motion in RoundMotion.objects.filter(round__tournament=tournament).select_related('motion').order_by('round_id', 'seq', 'id'):
        motion = round_motion.motion
        motions.setdefault(round_motion.round_id, []).append({
            'id': motion.id,
            'seq': round_motion.seq,
            'reference': motion.reference,
            'text': motion.text,
            'info_slide': motion.info_slide or '',
        })
    return [{
        'id': round_.id,
        'seq': round_.seq,
        'name': round_.name,
        'abbreviation': round_.abbreviation,
        'stage': 'elimination' if round_.stage == Round.Stage.ELIMINATION else 'preliminary',
        'break_category_id': round_.break_category_id if round_.stage == Round.Stage.ELIMINATION else None,
        'silent': round_.silent,
        'starts_at': timestamp_payload(round_.starts_at),
        'motions': motions.get(round_.id, []),
    } for round_ in rounds]


def _confirmed_ballots(tournament):
    """The confirmed, non-discarded ballot of each debate. Drafts, unconfirmed
    and discarded ballots are never exported."""
    ballots = {}
    queryset = BallotSubmission.objects.filter(
        confirmed=True, discarded=False, debate__round__tournament=tournament,
    ).select_related('debate').order_by('debate_id', 'version', 'id')
    for ballot in queryset:
        ballots[ballot.debate_id] = ballot  # Tabbycat allows one; keep the latest if not.
    return ballots


def _results_debates_payload(tournament, rounds):
    from draw.models import DebateTeam
    from results.models import CrossExaminationScore, SpeakerCriterionScore, SpeakerScore, TeamScore

    ballots = _confirmed_ballots(tournament)
    ballot_ids = [ballot.id for ballot in ballots.values()]
    round_seq = {round_.id: (round_.seq, round_.id) for round_ in rounds}
    reply_position = tournament.reply_position

    debate_teams = {}
    for debate_team in DebateTeam.objects.filter(debate_id__in=ballots).order_by('debate_id', 'side', 'id'):
        debate_teams.setdefault(debate_team.debate_id, []).append(debate_team)

    team_scores = {score.debate_team_id: score for score in TeamScore.objects.filter(ballot_submission_id__in=ballot_ids)}

    criteria = {}
    for criterion_score in SpeakerCriterionScore.objects.filter(
        speaker_score__ballot_submission_id__in=ballot_ids,
    ).select_related('criterion').order_by('speaker_score_id', 'criterion__seq', 'criterion_id'):
        criteria.setdefault(criterion_score.speaker_score_id, []).append(
            {'name': criterion_score.criterion.name, 'score': criterion_score.score})

    speeches = {}
    for speaker_score in SpeakerScore.objects.filter(ballot_submission_id__in=ballot_ids).order_by('debate_team_id', 'position', 'id'):
        speeches.setdefault(speaker_score.debate_team_id, []).append({
            'speaker_id': speaker_score.speaker_id,
            'position': speaker_score.position,
            'reply': reply_position is not None and speaker_score.position == reply_position,
            'score': speaker_score.score,
            'rank': speaker_score.rank,
            'ghost': speaker_score.ghost,
            'criteria': criteria.get(speaker_score.id, []),
        })

    cross_examinations = {}
    for cx_score in CrossExaminationScore.objects.filter(
        ballot_submission_id__in=ballot_ids,
    ).select_related('cross_examination').order_by('debate_team_id', 'cross_examination__seq', 'cross_examination_id'):
        cross_examinations.setdefault(cx_score.debate_team_id, []).append(
            {'name': cx_score.cross_examination.name, 'score': cx_score.score})

    panels = {}
    for allocation in DebateAdjudicator.objects.filter(debate_id__in=ballots):
        role = DEBATE_ROLE_NAMES.get(allocation.type)
        if role:
            panels.setdefault(allocation.debate_id, []).append({'adjudicator_id': allocation.adjudicator_id, 'role': role})

    payload = []
    ordered = sorted(ballots.values(), key=lambda ballot: (round_seq.get(ballot.debate.round_id, (0, 0)), ballot.debate_id))
    for ballot in ordered:
        debate = ballot.debate
        sides = []
        for debate_team in debate_teams.get(debate.id, []):
            team_score = team_scores.get(debate_team.id)
            sides.append({
                'team_id': debate_team.team_id,
                'side': debate_team.side,
                'side_name': _side_name(tournament, debate_team.side),
                'win': team_score.win if team_score else None,
                'points': team_score.points if team_score else None,
                'score': team_score.score if team_score else None,
                'votes_given': team_score.votes_given if team_score else None,
                'votes_possible': team_score.votes_possible if team_score else None,
                'speakers': speeches.get(debate_team.id, []),
                'cross_examination': cross_examinations.get(debate_team.id, []),
            })
        panel = sorted(panels.get(debate.id, []), key=lambda a: (DEBATE_ROLE_ORDER[a['role']], a['adjudicator_id']))
        payload.append({
            'id': debate.id,
            'round_id': debate.round_id,
            'motion_id': ballot.motion_id,
            'forfeit': ballot.forfeit,
            'teams': sides,
            'adjudicators': panel,
        })
    return payload, {a['adjudicator_id'] for debate in payload for a in debate['adjudicators']}


def _standing_entry(info, **identity):
    rank, tied = info.rankings.get('rank', (None, False))
    return {
        **identity,
        'rank': rank,
        'rank_tied': bool(tied) if rank is not None else False,
        'metrics': {str(key): _number(value) for key, value in info.metrics.items()},
    }


def _sorted_standings(entries, id_key):
    return sorted(entries, key=lambda e: (e['rank'] is None, e['rank'] or 0, e[id_key]))


def _rank_filter(tournament, last_round, preference, field):
    from tournaments.models import Round

    missable = tournament.pref(preference)
    if missable < 0:
        return None, None
    total = tournament.round_set.filter(stage=Round.Stage.PRELIMINARY, seq__lte=last_round.seq).count()
    return field, total - missable


def _results_standings_payload(tournament):
    """Team and speaker tabs after the last preliminary round, generated with
    the tournament's configured metrics (as on the admin standings pages)."""
    from participants.models import Speaker, Team
    from standings.base import StandingsError
    from standings.speakers import SpeakerStandingsGenerator
    from standings.teams import TeamStandingsGenerator

    last_round = tournament.prelim_rounds().order_by('seq').last()
    if last_round is None:
        return [], []

    try:
        team_metrics = list(tournament.pref('team_standings_precedence'))
        team_extra = list(tournament.pref('team_standings_extra_metrics'))
        teams = tournament.team_set.exclude(type=Team.TYPE_BYE).select_related('institution')
        team_standings = TeamStandingsGenerator(team_metrics, ('rank',), team_extra).generate(teams, round=last_round)
        team_payload = _sorted_standings(
            [_standing_entry(info, team_id=info.team.id) for info in team_standings], 'team_id')

        speaker_metrics = list(tournament.pref('speaker_standings_precedence'))
        speaker_extra = list(tournament.pref('speaker_standings_extra_metrics'))
        if tournament.pref('standings_missed_debates') >= 0 and 'count' not in speaker_metrics + speaker_extra:
            speaker_extra.append('count')
        speaker_filter = _rank_filter(tournament, last_round, 'standings_missed_debates', 'count')

        def speaker_tab(speakers, category_id):
            generator = SpeakerStandingsGenerator(speaker_metrics, ('rank',), speaker_extra,
                tournament=tournament, rank_filter=speaker_filter)
            standings = generator.generate(speakers.select_related('team', 'team__institution'), round=last_round)
            return _sorted_standings([_standing_entry(
                info, speaker_id=info.speaker.id, speaker_category_id=category_id, kind='substantive',
            ) for info in standings], 'speaker_id')

        speaker_payload = speaker_tab(Speaker.objects.filter(team__tournament=tournament), None)
        for category in tournament.speakercategory_set.order_by('seq', 'id'):
            speaker_payload.extend(speaker_tab(category.speaker_set.all(), category.id))

        reply_position = tournament.reply_position
        if reply_position is not None:
            repliers = Speaker.objects.filter(team__tournament=tournament, speakerscore__position=reply_position).distinct()
            generator = SpeakerStandingsGenerator(('replies_avg',), ('rank',), ('replies_stddev', 'replies_count'),
                tournament=tournament,
                rank_filter=_rank_filter(tournament, last_round, 'standings_missed_replies', 'replies_count'))
            standings = generator.generate(repliers.select_related('team', 'team__institution'), round=last_round)
            speaker_payload.extend(_sorted_standings([_standing_entry(
                info, speaker_id=info.speaker.id, speaker_category_id=None, kind='reply',
            ) for info in standings], 'speaker_id'))
    except StandingsError as exc:
        raise ValueError('Could not generate standings: %s' % exc) from exc
    return team_payload, speaker_payload


def _results_breaks_payload(tournament):
    from breakqual.models import BreakingTeam

    breaking = BreakingTeam.objects.filter(break_category__tournament=tournament).order_by(
        'break_category__seq', 'break_category_id', 'rank', 'team_id')
    return [{
        'break_category_id': row.break_category_id,
        'team_id': row.team_id,
        'rank': row.rank,
        'break_rank': row.break_rank,
        'remark': row.remark or None,
    } for row in breaking]


def build_results_payload(tournament, *, generated_at=None, idempotency_key=None):
    tournament = load_tournament_for_activity(tournament)
    break_tournament, season = break_tournament_metadata(tournament)
    rounds = list(tournament.round_set.order_by('seq', 'id'))

    # Side names are translated; build in the site language so the content,
    # and therefore the idempotency key, does not depend on the caller's locale.
    with translation.override(settings.LANGUAGE_CODE):
        rounds_payload = _results_rounds_payload(tournament, rounds)
        motion_ids = {motion['id'] for round_ in rounds_payload for motion in round_['motions']}
        debates, panel_adjudicator_ids = _results_debates_payload(tournament, rounds)
        for debate in debates:
            if debate['motion_id'] not in motion_ids:
                # A ballot can name a motion later detached from its round;
                # only motions listed under `rounds` may be referenced.
                debate['motion_id'] = None
        teams, team_institutions = _results_teams_payload(tournament, season)
        adjudicators, adjudicator_institutions = _results_adjudicators_payload(tournament, panel_adjudicator_ids)
        team_standings, speaker_standings = _results_standings_payload(tournament)
        payload = {
            'source_system': SOURCE_SYSTEM,
            'version': RESULTS_PAYLOAD_VERSION,
            'idempotency_key': idempotency_key,
            'generated_at': timestamp_payload(generated_at or timezone.now().replace(microsecond=0)),
            'tournament': _results_tournament_payload(tournament, rounds, break_tournament, season),
            'institutions': _results_institutions_payload(team_institutions + adjudicator_institutions),
            'break_categories': [{
                'id': category.id,
                'slug': category.slug,
                'name': category.name,
                'is_general': category.is_general,
                'break_size': category.break_size,
            } for category in tournament.breakcategory_set.order_by('seq', 'id')],
            'speaker_categories': [{
                'id': category.id,
                'slug': category.slug,
                'name': category.name,
            } for category in tournament.speakercategory_set.order_by('seq', 'id')],
            'teams': teams,
            'adjudicators': adjudicators,
            'rounds': rounds_payload,
            'debates': debates,
            'team_standings': team_standings,
            'speaker_standings': speaker_standings,
            'breaks': _results_breaks_payload(tournament),
        }
    return normalise_json_value(payload)


def validate_results_payload(payload):
    """Every reference must resolve inside the snapshot; DR imports it as one
    transaction, so a dangling ID would reject the whole tournament."""
    team_ids = {team['id'] for team in payload['teams']}
    speaker_ids = {speaker['id'] for team in payload['teams'] for speaker in team['speakers']}
    adjudicator_ids = {adjudicator['id'] for adjudicator in payload['adjudicators']}
    round_ids = {round_['id'] for round_ in payload['rounds']}
    motion_ids = {motion['id'] for round_ in payload['rounds'] for motion in round_['motions']}
    for team in payload['teams']:
        if not (team['name'] or '').strip():
            raise ValueError('Team %s has no name.' % team['id'])
        for speaker in team['speakers']:
            if not (speaker['name'] or '').strip():
                raise ValueError('Speaker %s has no name.' % speaker['id'])
    for debate in payload['debates']:
        if debate['round_id'] not in round_ids:
            raise ValueError('Debate %s refers to an unknown round.' % debate['id'])
        if debate['motion_id'] is not None and debate['motion_id'] not in motion_ids:
            raise ValueError('Debate %s refers to an unknown motion.' % debate['id'])
        for side in debate['teams']:
            if side['team_id'] not in team_ids:
                raise ValueError('Debate %s refers to an unknown team.' % debate['id'])
            for speech in side['speakers']:
                if speech['speaker_id'] not in speaker_ids:
                    raise ValueError('Debate %s refers to an unknown speaker.' % debate['id'])
        for allocation in debate['adjudicators']:
            if allocation['adjudicator_id'] not in adjudicator_ids:
                raise ValueError('Debate %s refers to an unknown adjudicator.' % debate['id'])
    return payload


def make_season_breaks_idempotency_key(season_id, published_at):
    """One key per published snapshot: a republish always gets a new key."""
    return '%s:season-breaks:%s:%s' % (SOURCE_SYSTEM, season_id, published_at)


def _published_snapshot(season):
    snapshot = season.public_snapshot
    if not isinstance(snapshot, dict) or not snapshot.get('published_at'):
        raise ValueError('Break season %s has no published snapshot. Publish it first.' % season.name)
    return snapshot


def season_breaks_sda_season(snapshot):
    """The SDA season (e.g. 2026/2027) named by the snapshot's season, or None.

    Read from the snapshot rather than the live season so the body stays
    identical for its key even if the season is renamed after publishing.
    DR derives the season from snapshot.published_at when this is missing.
    """
    season = snapshot.get('season') or {}
    for value in (season.get('name'), season.get('slug')):
        match = SEASON_LABEL_RE.search(value or '')
        if match:
            label = '%s/%s' % match.groups()
            if SDA_SEASON_RE.match(label):
                return label
    return None


def build_season_breaks_payload(season, *, generated_at=None):
    """The published snapshot exactly as stored, wrapped in the v1 envelope."""
    from seasonbreaks.models import BreakSeason
    if not isinstance(season, BreakSeason):
        season = BreakSeason.objects.get(pk=season)
    snapshot = _published_snapshot(season)
    payload = {
        'version': SEASON_BREAKS_PAYLOAD_VERSION,
        'source_system': SOURCE_SYSTEM,
        'generated_at': timestamp_payload(generated_at or timezone.now().replace(microsecond=0)),
        'snapshot': snapshot,
    }
    sda_season = season_breaks_sda_season(snapshot)
    if sda_season:
        payload['season'] = sda_season
    return payload


def validate_season_breaks_payload(payload):
    """The parts of DR's season-breaks contract it rejects outright."""
    snapshot = payload.get('snapshot')
    if not isinstance(snapshot, dict):
        raise ValueError('The season breaks payload has no snapshot.')
    if snapshot.get('version') != SEASON_BREAKS_SNAPSHOT_VERSION:
        raise ValueError('Unsupported break snapshot version %r. Republish the snapshot.' % snapshot.get('version'))
    season = snapshot.get('season')
    if not isinstance(season, dict):
        raise ValueError('The break snapshot has no season. Republish the snapshot.')
    for field in ('id', 'name', 'league', 'league_slug'):
        if season.get(field) in (None, ''):
            raise ValueError('The break snapshot has no season %s. Republish the snapshot.' % field)
    regions = snapshot.get('regions') or []
    if not isinstance(regions, list) or len(regions) > SEASON_BREAKS_MAX_REGIONS:
        raise ValueError('DR accepts at most %d regions per season.' % SEASON_BREAKS_MAX_REGIONS)
    if len(json.dumps(payload).encode('utf-8')) > SEASON_BREAKS_MAX_BYTES:
        raise ValueError('The break snapshot is larger than DR accepts (2.5 MB).')
    return payload


def payload_hash(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def feedback_export_queryset():
    from registration.models import Answer

    return AdjudicatorFeedback.objects.select_related(
        'adjudicator',
        'source_team__team__institution', 'source_team__debate__round__tournament',
        'source_adjudicator__adjudicator', 'source_adjudicator__debate__round__tournament',
    ).prefetch_related(Prefetch(
        'answers',
        queryset=Answer.objects.select_related('question', 'question__adjudicatorfeedbackquestion').order_by('question__seq', 'question__id'),
        to_attr='export_answers',
    ))


def load_feedback(feedback):
    if isinstance(feedback, AdjudicatorFeedback):
        return feedback
    return feedback_export_queryset().get(pk=feedback)


def _store_snapshot(model, payload, source_fields, *, force=False, reset_attempts=False, key=None):
    """One payload per content key, including unresolved versions of the same source.

    Queueing never sends or notifies a worker. Only an explicitly requested job can
    deliver these events. Existing payloads are immutable until acknowledged.
    """
    with transaction.atomic():
        event, created = model.objects.select_for_update().get_or_create(
            idempotency_key=key or payload['idempotency_key'],
            defaults={**source_fields, 'payload': payload, 'payload_hash': payload_hash(payload)},
        )
        # Do not reset a snapshot currently owned by another unfinished job.
        if event.job_items.exclude(job__status__in=['completed', 'completed_errors']).exists():
            return event
        source_field = model.export_source_field
        latest = model.objects.filter(
            **{source_field: source_fields[source_field]}, sent_at__isnull=False,
        ).order_by('-sent_at', '-id').first()
        if latest and latest.id == event.id and not force:
            # Compare with the last acknowledgement, including a failed force
            # attempt whose earlier acknowledgement remains valid.
            event.status = model.Status.SENT
            event.payload = None
            event.remote_response = None
            event.save(update_fields=['status', 'payload', 'remote_response'])
            return event
        if created or event.payload is None:
            event.payload = payload
            event.payload_hash = payload_hash(payload)
        event.status = model.Status.PENDING
        if reset_attempts:
            event.attempts = 0
        event.next_attempt_at = timezone.now()
        event.last_error = ''
        event.save()
        return event


def queue_feedback_export(feedback, *, force=False, reset_attempts=False):
    feedback = load_feedback(feedback)
    if not feedback.confirmed:
        return None
    payload = validate_feedback_payload(build_feedback_payload(feedback))
    content_hash = payload_hash({k: v for k, v in payload.items() if k != 'idempotency_key'})
    payload['idempotency_key'] = make_idempotency_key(feedback.id, content_hash)
    return _store_snapshot(FeedbackExportEvent, payload, {
        'feedback': feedback,
        'source_feedback_id': feedback.id,
        'source_tournament_id': feedback.adjudicator.tournament_id,
    }, force=force, reset_attempts=reset_attempts)


def queue_adjudicator_stats_export(tournament, *, force=False, reset_attempts=False):
    tournament = load_tournament_for_activity(tournament)
    payload = build_adjudicator_stats_payload(tournament)
    payload['idempotency_key'] = make_adjudicator_stats_idempotency_key(tournament, payload_hash(payload))
    return _store_snapshot(AdjudicatorStatsExportEvent, payload, {
        'tournament': tournament,
        'break_tournament_id': (payload['break_tournament'] or {}).get('id'),
        'source_tournament_id': tournament.id,
        'source_tournament_slug': tournament.slug,
        'source_tournament_name': tournament.name,
        'source_tournament_short_name': tournament.short_name,
    }, force=force, reset_attempts=reset_attempts)


def queue_results_export(tournament, *, force=False, reset_attempts=False):
    tournament = load_tournament_for_activity(tournament)
    payload = validate_results_payload(build_results_payload(tournament))
    key = make_results_idempotency_key(tournament, results_content_hash(payload))
    # Reuse the build time of an already prepared version of this content so a
    # resend under the same key carries a byte-identical body.
    generated_at = ResultsExportEvent.objects.filter(idempotency_key=key).values_list('generated_at', flat=True).first()
    generated_at = generated_at or timezone.now().replace(microsecond=0)
    payload['idempotency_key'] = key
    payload['generated_at'] = timestamp_payload(generated_at)
    return _store_snapshot(ResultsExportEvent, payload, {
        'tournament': tournament,
        'source_tournament_id': tournament.id,
        'source_tournament_slug': tournament.slug,
        'source_tournament_name': tournament.name,
        'source_tournament_short_name': tournament.short_name,
        'generated_at': generated_at,
    }, force=force, reset_attempts=reset_attempts)


def queue_season_breaks_export(season, *, force=False, reset_attempts=False):
    """Freeze a season's published snapshot as a DR delivery (no network I/O)."""
    from seasonbreaks.models import BreakSeason
    if not isinstance(season, BreakSeason):
        season = BreakSeason.objects.get(pk=season)
    snapshot = _published_snapshot(season)
    key = make_season_breaks_idempotency_key(season.id, snapshot['published_at'])
    generated_at = SeasonBreaksExportEvent.objects.filter(idempotency_key=key).values_list('generated_at', flat=True).first()
    generated_at = generated_at or timezone.now().replace(microsecond=0)
    payload = validate_season_breaks_payload(build_season_breaks_payload(season, generated_at=generated_at))
    return _store_snapshot(SeasonBreaksExportEvent, payload, {
        'season': season,
        'source_season_id': season.id,
        'source_season_slug': season.slug,
        'source_season_name': season.name,
        'published_at': season.public_published_at,
        'generated_at': generated_at,
    }, force=force, reset_attempts=reset_attempts, key=key)


def retry_delay(attempts):
    seconds = min(60 * 2 ** max(attempts - 1, 0), 3600)
    return timezone.now() + timedelta(seconds=seconds * random.uniform(0.8, 1.2))


def truncate_bytes(value, limit):
    return str(value).encode('utf-8')[:limit].decode('utf-8', errors='ignore')


def parse_response_body(body):
    if not body:
        return None
    try:
        return json.loads(body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return {'raw': body.decode('utf-8', errors='replace')}


def summarise_response_body(response_body, *, limit=300):
    if not response_body:
        return ''
    text = response_body
    if isinstance(response_body, dict):
        for key in ('detail', 'message', 'error', 'errors', 'raw'):
            if response_body.get(key):
                text = response_body[key]
                break
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False, sort_keys=True)
    return truncate_bytes(text.strip(), limit)


def compact_receipt(response_body):
    receipt = {'summary': 'Accepted by DR'}
    if isinstance(response_body, dict):
        for key in ('message', 'detail', 'status'):
            if isinstance(response_body.get(key), str):
                receipt['summary'] = truncate_bytes(response_body[key], 256)
                break
    if isinstance(response_body, dict):
        for key in ('id', 'remote_id', 'import_id'):
            if response_body.get(key) is not None:
                receipt[key] = truncate_bytes(response_body[key], 128)
    return receipt


def bounded_diagnostic(response_body):
    if len(json.dumps(response_body, ensure_ascii=False).encode('utf-8')) <= 4096:
        return response_body
    # Account for JSON escaping in the byte limit as well as multibyte text.
    text = summarise_response_body(response_body, limit=3000)
    while len(json.dumps({'detail': text}, ensure_ascii=False).encode('utf-8')) > 4096:
        text = text[:len(text) // 2]
    return {'detail': text}


# Compatibility entry points create durable jobs; none perform network I/O.
def send_event(event, *, dry_run=False):
    from .jobs import create_backlog_job
    if not dry_run and event.status != event.Status.SENT:
        create_backlog_job(kinds=['feedback'], event_ids={'feedback': [event.id]})
    return event


def send_adjudicator_stats_event(event, *, dry_run=False):
    from .jobs import create_backlog_job
    if not dry_run and event.status != event.Status.SENT:
        create_backlog_job(kinds=['activity'], event_ids={'activity': [event.id]})
    return event


def send_results_event(event, *, dry_run=False):
    from .jobs import create_backlog_job
    if not dry_run and event.status != event.Status.SENT:
        create_backlog_job(kinds=['results'], event_ids={'results': [event.id]})
    return event


def send_pending_events(*, event_ids=None, limit=50, dry_run=False):
    from .jobs import create_backlog_job
    if dry_run:
        return {'pending': FeedbackExportEvent.objects.exclude(status='sent').count()}
    job = create_backlog_job(kinds=['feedback'], event_ids={'feedback': event_ids} if event_ids else None)
    return {'job_id': job.id}


def send_pending_adjudicator_stats_events(*, event_ids=None, limit=50, dry_run=False):
    from .jobs import create_backlog_job
    if dry_run:
        return {'pending': AdjudicatorStatsExportEvent.objects.exclude(status='sent').count()}
    job = create_backlog_job(kinds=['activity'], event_ids={'activity': event_ids} if event_ids else None)
    return {'job_id': job.id}


def queue_confirmed_feedback(queryset=None, *, force=False, reset_attempts=False):
    from .jobs import create_job
    queryset = queryset if queryset is not None else AdjudicatorFeedback.objects.filter(confirmed=True)
    ids = list(queryset.values_list('adjudicator__tournament_id', flat=True).distinct())
    job = create_job(tournament_ids=ids, kinds=['feedback'], force=force)
    return {'job_id': job.id}


def stream_configuration(kind):
    """(enabled, endpoint, token, timeout setting name) for one export stream."""
    if kind == 'activity':
        return (adjudicator_stats_export_enabled(), adjudicator_stats_export_endpoint(),
                adjudicator_stats_export_token(), 'ADJUDICATOR_STATS_EXPORT_TIMEOUT')
    if kind == 'results':
        return results_export_enabled(), results_export_endpoint(), results_export_token(), 'RESULTS_EXPORT_TIMEOUT'
    if kind == 'breaks':
        return (season_breaks_export_enabled(), season_breaks_export_endpoint(), season_breaks_export_token(),
                'SEASON_BREAKS_EXPORT_TIMEOUT')
    return feedback_export_enabled(), feedback_export_endpoint(), feedback_export_token(), 'FEEDBACK_EXPORT_TIMEOUT'


def encode_request_body(payload, kind):
    """JSON body bytes and extra headers; large results snapshots are gzipped.

    DR accepts gzip only on the results endpoint, so other streams send plain JSON.
    """
    body = json.dumps(payload, sort_keys=True).encode('utf-8')
    if kind == 'results' and len(body) > RESULTS_GZIP_THRESHOLD:
        # mtime=0 keeps the compressed bytes identical across retries.
        return gzip.compress(body, mtime=0), {'Content-Encoding': 'gzip'}
    return body, {}


NEW_ENDPOINT_SETTINGS = {
    'results': 'SDA_JUDGES_RESULTS_API_URL',
    'breaks': 'SDA_JUDGES_SEASON_BREAKS_API_URL',
}


def deliver_snapshot(event, kind):
    """HTTP transport only. The worker commits this result under its claim fence."""
    import time
    from email.utils import parsedate_to_datetime

    enabled, endpoint, token, timeout_name = stream_configuration(kind)
    if not enabled or not endpoint:
        return {'status': 'blocked', 'error': 'Export is disabled or its API endpoint is not configured.'}
    if not event.payload:
        return {'status': 'failed', 'error': 'No prepared payload remains. Start a new export from the source tournament.'}

    def read_body(response):
        # Bound both memory and time; do not consume arbitrary HTML error pages.
        deadline = time.monotonic() + 30
        chunks = []
        remaining = 4096
        while remaining and time.monotonic() < deadline:
            chunk = response.read1(remaining) if hasattr(response, 'read1') else response.read(remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        return parse_response_body(b''.join(chunks))

    headers = {
        'Content-Type': 'application/json', 'Accept': 'application/json',
        'User-Agent': 'Tabbycat DR Export', 'Idempotency-Key': event.idempotency_key,
    }
    if token:
        headers['Authorization'] = 'Bearer %s' % token
    try:
        body, extra_headers = encode_request_body(event.payload, kind)
        headers.update(extra_headers)
        request = urllib.request.Request(endpoint, data=body, headers=headers, method='POST')
        timeout = max(1, min(int(getattr(settings, timeout_name, DEFAULT_TIMEOUT)), 30))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = read_body(response)
            if response.status in {200, 201}:
                receipt = compact_receipt(body)
                if token:
                    receipt = {key: value.replace(token, '[redacted]') for key, value in receipt.items()}
                return {'status': 'sent', 'http_status': response.status, 'receipt': receipt}
            return {'status': 'retry', 'http_status': response.status, 'error': 'DR returned an unexpected acknowledgement.'}
    except urllib.error.HTTPError as exc:
        try:
            body = read_body(exc)
        except Exception:
            body = None
        finally:
            exc.close()
        detail = summarise_response_body(body, limit=1800)
        if token:
            detail = detail.replace(token, '[redacted]')
        status = 'blocked' if exc.code in {401, 403} else ('retry' if exc.code == 429 or exc.code >= 500 else 'failed')
        error = 'DR returned HTTP %s. %s' % (exc.code, detail)
        if kind in NEW_ENDPOINT_SETTINGS and exc.code == 404:
            # These endpoints are new in DR: a 404 means a wrong URL or an
            # undeployed receiver, so hold the stream instead of failing records.
            status = 'blocked'
            error = 'DR has no %s endpoint at the configured URL (HTTP 404). Check %s and that DR supports these imports, then resume. %s' % (
                kind if kind == 'results' else 'season breaks', NEW_ENDPOINT_SETTINGS[kind], detail)
        if exc.code == 409:
            error = 'DR reported a conflict (HTTP 409). Inspect this record before retrying. ' + detail
        result = {'status': status, 'http_status': exc.code, 'error': truncate_bytes(error, 2048),
                  'diagnostic': bounded_diagnostic({'detail': detail})}
        if (exc.code == 429 or exc.code >= 500) and exc.headers:
            value = exc.headers.get('Retry-After')
            if value:
                try:
                    result['retry_at'] = timezone.now() + timedelta(seconds=max(0, int(value)))
                except (ValueError, OverflowError):
                    try:
                        result['retry_at'] = parsedate_to_datetime(value)
                        if timezone.is_naive(result['retry_at']):
                            result['retry_at'] = timezone.make_aware(result['retry_at'])
                    except (ValueError, TypeError, OverflowError):
                        pass
        return result
    except (ValueError, TypeError):
        return {'status': 'blocked', 'error': 'Invalid export endpoint or timeout configuration.'}
    except Exception:
        # Exception strings may contain URLs, credentials or request data.
        return {'status': 'retry', 'error': 'Could not reach DR or read its response. The same snapshot will be retried.'}
