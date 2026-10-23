import hashlib
import json
import logging
import random
import re
import urllib.error
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.text import slugify

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


def _store_snapshot(model, payload, source_fields, *, force=False, reset_attempts=False):
    """One payload per content key, including unresolved versions of the same source.

    Queueing never sends or notifies a worker. Only an explicitly requested job can
    deliver these events. Existing payloads are immutable until acknowledged.
    """
    with transaction.atomic():
        event, created = model.objects.select_for_update().get_or_create(
            idempotency_key=payload['idempotency_key'],
            defaults={**source_fields, 'payload': payload, 'payload_hash': payload_hash(payload)},
        )
        # Do not reset a snapshot currently owned by another unfinished job.
        if event.job_items.exclude(job__status__in=['completed', 'completed_errors']).exists():
            return event
        source_field = 'source_feedback_id' if model is FeedbackExportEvent else 'source_tournament_id'
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


def deliver_snapshot(event, kind):
    """HTTP transport only. The worker commits this result under its claim fence."""
    import time
    from email.utils import parsedate_to_datetime

    activity = kind == 'activity'
    enabled = adjudicator_stats_export_enabled() if activity else feedback_export_enabled()
    endpoint = adjudicator_stats_export_endpoint() if activity else feedback_export_endpoint()
    token = adjudicator_stats_export_token() if activity else feedback_export_token()
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
        request = urllib.request.Request(endpoint, data=json.dumps(event.payload, sort_keys=True).encode('utf-8'), headers=headers, method='POST')
        timeout_name = 'ADJUDICATOR_STATS_EXPORT_TIMEOUT' if activity else 'FEEDBACK_EXPORT_TIMEOUT'
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
