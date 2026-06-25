import hashlib
import json
import logging
import re
import urllib.error
import urllib.request
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.text import slugify
from django.utils import timezone

from adjallocation.models import DebateAdjudicator
from adjfeedback.models import AdjudicatorFeedback
from results.models import BallotSubmission
from tournaments.models import Tournament

from .models import AdjudicatorStatsExportEvent, FeedbackExportEvent

logger = logging.getLogger(__name__)

SOURCE_SYSTEM = 'tabbycat-sda'
DEFAULT_TIMEOUT = 10
MAX_ATTEMPTS = 8
SEASON_LABEL_RE = re.compile(r'(20\d{2})\s*[/-]\s*(20\d{2})')


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
    for answer in feedback.answers.select_related('question').order_by('question__seq', 'question__id'):
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
        return Tournament.objects.get(pk=tournament.pk)
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
    payload = build_adjudicator_stats_payload(
        tournament,
        idempotency_key=make_adjudicator_stats_idempotency_key(tournament, content_hash),
    )
    return payload_hash(payload)


def adjudicator_stats_event_needs_reexport(event, tournament=None):
    if event is None or event.status != AdjudicatorStatsExportEvent.Status.SENT:
        return False
    tournament = tournament or event.tournament
    if tournament is None:
        return False
    return event.payload_hash != adjudicator_stats_content_hash(tournament)


def payload_hash(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def load_feedback(feedback):
    if isinstance(feedback, AdjudicatorFeedback):
        return feedback
    return AdjudicatorFeedback.objects.select_related(
        'adjudicator', 'adjudicator__institution', 'adjudicator__institution__region',
        'source_team', 'source_team__team', 'source_team__team__institution', 'source_team__team__institution__region',
        'source_team__debate', 'source_team__debate__round', 'source_team__debate__round__tournament',
        'source_adjudicator', 'source_adjudicator__adjudicator', 'source_adjudicator__adjudicator__institution',
        'source_adjudicator__adjudicator__institution__region',
        'source_adjudicator__debate', 'source_adjudicator__debate__round', 'source_adjudicator__debate__round__tournament',
    ).prefetch_related('answers__question').get(pk=feedback)


def queue_feedback_export(feedback, *, force=False, reset_attempts=False):
    feedback = load_feedback(feedback)
    if not feedback.confirmed and not force:
        return None

    with transaction.atomic():
        event, _ = FeedbackExportEvent.objects.select_for_update().get_or_create(
            feedback=feedback,
            defaults={'idempotency_key': make_idempotency_key(feedback.id)},
        )

        try:
            payload = build_feedback_payload(feedback)
            validate_feedback_payload(payload)
        except Exception as exc:
            logger.exception('Failed to build feedback export payload for feedback %s', feedback.id)
            event.mark_failed(exc, retry_at=retry_delay(event.attempts))
            return event

        # Content-addressed idempotency key: it changes whenever the exported content
        # changes, so DR records each update as a fresh import (upserting the feedback by
        # source id) instead of rejecting a same-key/changed-data resend with HTTP 409.
        content_hash = payload_hash({k: v for k, v in payload.items() if k != 'idempotency_key'})
        idempotency_key = make_idempotency_key(feedback.id, content_hash)
        payload['idempotency_key'] = idempotency_key
        event.idempotency_key = idempotency_key

        new_hash = payload_hash(payload)
        if event.status == FeedbackExportEvent.Status.SENT and event.payload_hash == new_hash and not force:
            return event

        event.payload = payload
        event.payload_hash = new_hash
        event.status = FeedbackExportEvent.Status.PENDING
        if reset_attempts:
            event.attempts = 0
        event.last_error = ''
        event.last_http_status = None
        event.remote_response = None
        event.next_attempt_at = timezone.now()
        event.sent_at = None
        event.save(update_fields=[
            'idempotency_key', 'payload', 'payload_hash', 'status', 'attempts', 'last_error',
            'last_http_status', 'remote_response', 'next_attempt_at', 'sent_at', 'updated_at',
        ])

    if feedback_export_enabled():
        notify_feedback_export_worker([event.id])
    return event


def notify_feedback_export_worker(event_ids=None):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.send)('feedbackexport', {
        'type': 'feedback.export',
        'event_ids': event_ids or [],
    })


def notify_adjudicator_stats_export_worker(event_ids=None):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.send)('feedbackexport', {
        'type': 'adjudicator.stats.export',
        'event_ids': event_ids or [],
    })


def retry_delay(attempts):
    minutes = min(2 ** max(attempts - 1, 0), 60)
    return timezone.now() + timedelta(minutes=minutes)


def parse_response_body(body):
    if not body:
        return None
    try:
        return json.loads(body.decode('utf-8'))
    except Exception:
        return {'raw': body.decode('utf-8', errors='replace')}


def summarise_response_body(response_body, *, limit=300):
    """Distil DR's response into a short human-readable string for last_error."""
    if not response_body:
        return ''
    text = None
    if isinstance(response_body, dict):
        for key in ('detail', 'message', 'error', 'errors', 'raw'):
            if response_body.get(key):
                text = response_body[key]
                break
        else:
            text = response_body
    else:
        text = response_body
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False, sort_keys=True)
    return text.strip()[:limit]


def send_event(event, *, dry_run=False):
    if event.status == FeedbackExportEvent.Status.SENT and not dry_run:
        return event
    if not event.payload:
        queue_feedback_export(event.feedback, force=True)
        event.refresh_from_db()
    if event.status == FeedbackExportEvent.Status.PERMANENT_FAILED:
        return event

    endpoint = feedback_export_endpoint()
    if not endpoint:
        if dry_run:
            return event
        event.attempts += 1
        event.save(update_fields=['attempts', 'updated_at'])
        event.mark_failed('FEEDBACK_EXPORT_ENDPOINT is not configured.', retry_at=retry_delay(event.attempts))
        return event

    if dry_run:
        return event

    token = feedback_export_token()
    body = json.dumps(event.payload, sort_keys=True).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Tabbycat Feedback Export',
        'Idempotency-Key': event.idempotency_key,
    }
    if token:
        headers['Authorization'] = 'Bearer %s' % token

    request = urllib.request.Request(endpoint, data=body, headers=headers, method='POST')
    event.attempts += 1
    event.save(update_fields=['attempts', 'updated_at'])

    try:
        timeout = int(getattr(settings, 'FEEDBACK_EXPORT_TIMEOUT', DEFAULT_TIMEOUT))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = parse_response_body(response.read())
            if response.status in {200, 201}:
                event.mark_sent(response_data=response_body, http_status=response.status)
            else:
                event.mark_failed(
                    'External feedback API returned unexpected HTTP %s.' % response.status,
                    http_status=response.status,
                    retry_at=retry_delay(event.attempts),
                )
    except urllib.error.HTTPError as exc:
        response_body = parse_response_body(exc.read())
        event.remote_response = response_body
        event.save(update_fields=['remote_response', 'updated_at'])
        if exc.code in {401, 403}:
            logger.error('Invalid SDA judges API token while exporting feedback event %s', event.id)
        permanent = 400 <= exc.code < 500 and exc.code not in {409, 429}
        detail = summarise_response_body(response_body)
        message = 'External feedback API returned HTTP %s.' % exc.code
        if detail:
            message = '%s %s' % (message, detail)
        event.mark_failed(
            message,
            permanent=permanent,
            http_status=exc.code,
            retry_at=retry_delay(event.attempts),
        )
    except Exception as exc:
        logger.exception('Failed to export feedback event %s', event.id)
        event.mark_failed(exc, retry_at=retry_delay(event.attempts))
    return event


def _update_adjudicator_stats_event_source_fields(event, tournament, break_tournament=None):
    event.tournament = tournament
    event.break_tournament = break_tournament
    event.source_tournament_id = tournament.id
    event.source_tournament_slug = tournament.slug
    event.source_tournament_name = tournament.name
    event.source_tournament_short_name = tournament.short_name


def queue_adjudicator_stats_export(tournament, *, force=False, reset_attempts=False):
    tournament = load_tournament_for_activity(tournament)
    break_tournament, _season = break_tournament_metadata(tournament)
    with transaction.atomic():
        event = AdjudicatorStatsExportEvent.objects.select_for_update().filter(
            source_tournament_id=tournament.id,
        ).order_by('id').first()
        if event is None:
            event = AdjudicatorStatsExportEvent(
                tournament=tournament,
                source_tournament_id=tournament.id,
                idempotency_key=make_adjudicator_stats_idempotency_key(tournament),
            )
        is_new_event = event.pk is None
        _update_adjudicator_stats_event_source_fields(event, tournament, break_tournament)
        content_payload = build_adjudicator_stats_payload(tournament, idempotency_key='')
        content_hash = payload_hash(content_payload)
        idempotency_key = make_adjudicator_stats_idempotency_key(tournament, content_hash)
        payload = build_adjudicator_stats_payload(tournament, idempotency_key=idempotency_key)
        new_hash = payload_hash(payload)

        if event.status == AdjudicatorStatsExportEvent.Status.SENT and event.payload_hash == new_hash and not force:
            event.save(update_fields=[
                'tournament', 'break_tournament', 'source_tournament_id', 'source_tournament_slug',
                'source_tournament_name', 'source_tournament_short_name', 'updated_at',
            ])
            return event

        event.idempotency_key = idempotency_key
        event.payload = payload
        event.payload_hash = new_hash
        event.status = AdjudicatorStatsExportEvent.Status.PENDING
        if reset_attempts:
            event.attempts = 0
        event.last_error = ''
        event.last_http_status = None
        event.remote_response = None
        event.next_attempt_at = timezone.now()
        event.sent_at = None
        if is_new_event:
            event.save()
        else:
            event.save(update_fields=[
                'tournament', 'break_tournament', 'source_tournament_id', 'source_tournament_slug',
                'source_tournament_name', 'source_tournament_short_name', 'idempotency_key', 'payload',
                'payload_hash', 'status', 'attempts', 'last_error', 'last_http_status', 'remote_response',
                'next_attempt_at', 'sent_at', 'updated_at',
            ])

    if adjudicator_stats_export_enabled():
        notify_adjudicator_stats_export_worker([event.id])
    return event


def send_adjudicator_stats_event(event, *, dry_run=False):
    if event.status == AdjudicatorStatsExportEvent.Status.SENT and not dry_run:
        return event
    if not event.payload:
        if event.tournament_id:
            queue_adjudicator_stats_export(event.tournament, force=True)
            event.refresh_from_db()
        else:
            event.mark_failed(
                'Cannot rebuild judge activity payload because the source tournament no longer exists.',
                permanent=True,
            )
            return event
    if event.status == AdjudicatorStatsExportEvent.Status.PERMANENT_FAILED:
        return event

    endpoint = adjudicator_stats_export_endpoint()
    if not endpoint:
        if dry_run:
            return event
        event.attempts += 1
        event.save(update_fields=['attempts', 'updated_at'])
        event.mark_failed('ADJUDICATOR_STATS_EXPORT_ENDPOINT is not configured.', retry_at=retry_delay(event.attempts))
        return event

    if dry_run:
        return event

    token = adjudicator_stats_export_token()
    body = json.dumps(event.payload, sort_keys=True).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Tabbycat Judge Activity Export',
        'Idempotency-Key': event.idempotency_key,
    }
    if token:
        headers['Authorization'] = 'Bearer %s' % token

    request = urllib.request.Request(endpoint, data=body, headers=headers, method='POST')
    event.attempts += 1
    event.save(update_fields=['attempts', 'updated_at'])

    try:
        timeout = int(getattr(settings, 'ADJUDICATOR_STATS_EXPORT_TIMEOUT', DEFAULT_TIMEOUT))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = parse_response_body(response.read())
            if response.status in {200, 201}:
                event.mark_sent(response_data=response_body, http_status=response.status)
            else:
                event.mark_failed(
                    'External adjudicator stats API returned unexpected HTTP %s.' % response.status,
                    http_status=response.status,
                    retry_at=retry_delay(event.attempts),
                )
    except urllib.error.HTTPError as exc:
        response_body = parse_response_body(exc.read())
        event.remote_response = response_body
        event.save(update_fields=['remote_response', 'updated_at'])
        if exc.code in {401, 403}:
            logger.error('Invalid SDA judges API token while exporting adjudicator stats event %s', event.id)
        permanent = 400 <= exc.code < 500 and exc.code not in {409, 429}
        detail = summarise_response_body(response_body)
        message = 'External adjudicator stats API returned HTTP %s.' % exc.code
        if detail:
            message = '%s %s' % (message, detail)
        event.mark_failed(
            message,
            permanent=permanent,
            http_status=exc.code,
            retry_at=retry_delay(event.attempts),
        )
    except Exception as exc:
        logger.exception('Failed to export adjudicator stats event %s', event.id)
        event.mark_failed(exc, retry_at=retry_delay(event.attempts))
    return event


def pending_events_queryset(event_ids=None):
    now = timezone.now()
    queryset = FeedbackExportEvent.objects.select_related('feedback').filter(
        status__in=[FeedbackExportEvent.Status.PENDING, FeedbackExportEvent.Status.FAILED],
    ).filter(attempts__lt=MAX_ATTEMPTS).filter(
        models_Q_next_attempt(now)
    )
    if event_ids:
        queryset = queryset.filter(id__in=event_ids)
    return queryset.order_by('next_attempt_at', 'created_at')


def pending_adjudicator_stats_events_queryset(event_ids=None):
    now = timezone.now()
    queryset = AdjudicatorStatsExportEvent.objects.select_related('tournament', 'break_tournament').filter(
        status__in=[AdjudicatorStatsExportEvent.Status.PENDING, AdjudicatorStatsExportEvent.Status.FAILED],
    ).filter(attempts__lt=MAX_ATTEMPTS).filter(
        models_Q_next_attempt(now)
    )
    if event_ids:
        queryset = queryset.filter(id__in=event_ids)
    return queryset.order_by('next_attempt_at', 'created_at')


def models_Q_next_attempt(now):
    from django.db.models import Q
    return Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now)


def send_pending_events(*, event_ids=None, limit=50, dry_run=False):
    queryset = pending_events_queryset(event_ids=event_ids)[:limit]
    sent = failed = pending = 0
    events = list(queryset)
    for event in events:
        before = event.status
        send_event(event, dry_run=dry_run)
        event.refresh_from_db()
        if dry_run:
            pending += 1
        elif event.status == FeedbackExportEvent.Status.SENT:
            sent += 1
        elif event.status in {FeedbackExportEvent.Status.FAILED, FeedbackExportEvent.Status.PERMANENT_FAILED}:
            failed += 1
        elif event.status == before:
            pending += 1
    return {'processed': len(events), 'sent': sent, 'failed': failed, 'pending': pending}


def send_pending_adjudicator_stats_events(*, event_ids=None, limit=50, dry_run=False):
    queryset = pending_adjudicator_stats_events_queryset(event_ids=event_ids)[:limit]
    sent = failed = pending = 0
    events = list(queryset)
    for event in events:
        before = event.status
        send_adjudicator_stats_event(event, dry_run=dry_run)
        event.refresh_from_db()
        if dry_run:
            pending += 1
        elif event.status == AdjudicatorStatsExportEvent.Status.SENT:
            sent += 1
        elif event.status in {AdjudicatorStatsExportEvent.Status.FAILED, AdjudicatorStatsExportEvent.Status.PERMANENT_FAILED}:
            failed += 1
        elif event.status == before:
            pending += 1
    return {'processed': len(events), 'sent': sent, 'failed': failed, 'pending': pending}


def queue_confirmed_feedback(queryset=None, *, force=False, reset_attempts=False):
    if queryset is None:
        queryset = AdjudicatorFeedback.objects.filter(confirmed=True)
    queryset = queryset.filter(confirmed=True).select_related('adjudicator')
    queued = skipped = 0
    for feedback in queryset.iterator():
        event = queue_feedback_export(feedback, force=force, reset_attempts=reset_attempts)
        if event is None:
            skipped += 1
        else:
            queued += 1
    return {'queued': queued, 'skipped': skipped}
