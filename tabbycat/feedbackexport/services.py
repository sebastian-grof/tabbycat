import hashlib
import json
import logging
import urllib.error
import urllib.request
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from adjfeedback.models import AdjudicatorFeedback

from .models import FeedbackExportEvent, JudgeProfile, JudgeProfileLink

logger = logging.getLogger(__name__)

SOURCE_SYSTEM = 'tabbycat-sda'
DEFAULT_TIMEOUT = 10
MAX_ATTEMPTS = 8


class FeedbackExportError(RuntimeError):
    pass


class MissingJudgeProfile(FeedbackExportError):
    pass


def feedback_export_enabled():
    return bool(getattr(settings, 'FEEDBACK_EXPORT_ENABLED', False))


def feedback_export_endpoint():
    return getattr(settings, 'FEEDBACK_EXPORT_ENDPOINT', '')


def feedback_export_token():
    return getattr(settings, 'FEEDBACK_EXPORT_TOKEN', '')


def make_idempotency_key(feedback_id):
    return '%s:feedback:%s:v1' % (SOURCE_SYSTEM, feedback_id)


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


def judge_profile_payload(profile):
    return {
        'id': profile.id,
        'external_id': profile.external_id,
        'export_id': profile.export_id,
        'name': profile.name,
        'primary_email': profile.primary_email,
        'active': profile.active,
    }


def adjudicator_payload(adjudicator, *, include_profile=True):
    payload = {
        'local_id': adjudicator.id,
        'name': adjudicator.name,
        'email': adjudicator.email,
        'institution': participant_institution_payload(adjudicator.institution),
    }
    if include_profile:
        try:
            payload['judge_profile'] = judge_profile_payload(adjudicator.judge_profile_link.profile)
        except JudgeProfileLink.DoesNotExist:
            payload['judge_profile'] = None
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
    payload = {
        'type': 'adjudicator',
        'local_id': debate_adjudicator.adjudicator_id,
        'display_name': debate_adjudicator.adjudicator.name,
    }
    if debate_adjudicator.adjudicator.email:
        payload['email'] = debate_adjudicator.adjudicator.email
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


def answers_payload(feedback):
    answers = []
    for answer in feedback.answers.select_related('question').order_by('question__seq', 'question__id'):
        question = answer.question
        try:
            value = answer.deserialize_answer()
        except Exception:
            logger.exception('Could not deserialize feedback answer %s', answer.id)
            value = answer.answer
        value = normalise_json_value(value)
        answers.append({
            'question_reference': getattr(question, 'reference', None),
            'question_text': question.text,
            'answer_type': answer_type_payload(question),
            'raw_value': value,
            'value': value,
        })
    return answers


def timestamp_payload(value):
    return value.isoformat() if value else None


def tournament_season_payload(tournament):
    try:
        break_tournament = tournament.break_tournaments.select_related('season').order_by(
            '-season__active', '-season__created_at',
        ).first()
    except Exception:
        logger.exception('Could not resolve feedback export season for tournament %s', tournament.id)
        return None
    if not break_tournament:
        return None
    return break_tournament.season.name


def build_feedback_payload(feedback):
    feedback = load_feedback(feedback)
    try:
        profile = feedback.adjudicator.judge_profile_link.profile
    except JudgeProfileLink.DoesNotExist as exc:
        raise MissingJudgeProfile(
            'Target adjudicator %s (#%s) is not linked to a judge profile.' % (feedback.adjudicator.name, feedback.adjudicator_id)
        ) from exc

    debate = feedback.debate
    round_ = debate.round
    tournament = round_.tournament
    debate_adjudicator = feedback.debate_adjudicator

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
        'score': feedback.score,
        'tournament': {
            'id': tournament.id,
            'slug': tournament.slug,
            'name': tournament.name,
            'short_name': tournament.short_name,
            'season': tournament_season_payload(tournament),
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
            'judge_profile_id': profile.export_id,
            'local_adjudicator_id': feedback.adjudicator_id,
            'name': feedback.adjudicator.name,
            'email': feedback.adjudicator.email,
            'role': debate_adjudicator_role(debate_adjudicator),
        },
        'source': source_payload(feedback),
        'answers': answers_payload(feedback),
    }


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
        if event.idempotency_key != make_idempotency_key(feedback.id):
            event.idempotency_key = make_idempotency_key(feedback.id)

        try:
            payload = build_feedback_payload(feedback)
        except MissingJudgeProfile as exc:
            event.payload = None
            event.payload_hash = ''
            event.remote_response = None
            event.status = FeedbackExportEvent.Status.PERMANENT_FAILED
            event.last_error = str(exc)
            event.last_http_status = None
            event.next_attempt_at = None
            event.save(update_fields=[
                'payload', 'payload_hash', 'remote_response', 'status', 'last_error',
                'last_http_status', 'next_attempt_at', 'updated_at',
            ])
            return event

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
        event.mark_failed(
            'External feedback API returned HTTP %s.' % exc.code,
            permanent=permanent,
            http_status=exc.code,
            retry_at=retry_delay(event.attempts),
        )
    except Exception as exc:
        logger.exception('Failed to export feedback event %s', event.id)
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


def queue_confirmed_feedback(queryset=None, *, force=False, reset_attempts=False):
    if queryset is None:
        queryset = AdjudicatorFeedback.objects.filter(confirmed=True)
    queryset = queryset.filter(confirmed=True).select_related('adjudicator')
    queued = skipped = blocked = 0
    for feedback in queryset.iterator():
        event = queue_feedback_export(feedback, force=force, reset_attempts=reset_attempts)
        if event is None:
            skipped += 1
        elif event.status == FeedbackExportEvent.Status.PERMANENT_FAILED:
            blocked += 1
        else:
            queued += 1
    return {'queued': queued, 'skipped': skipped, 'blocked': blocked}


def auto_create_profiles_from_adjudicators(adjudicators):
    created_profiles = created_links = existing_links = 0
    for adjudicator in adjudicators:
        if hasattr(adjudicator, 'judge_profile_link'):
            existing_links += 1
            continue
        profile = None
        email = (adjudicator.email or '').strip().lower()
        if email:
            matches = [p for p in JudgeProfile.objects.filter(primary_email__iexact=email)]
            if len(matches) == 1:
                profile = matches[0]
        if profile is None:
            profile = JudgeProfile.objects.create(
                name=adjudicator.name,
                primary_email=adjudicator.email or None,
            )
            created_profiles += 1
        JudgeProfileLink.objects.create(profile=profile, adjudicator=adjudicator)
        created_links += 1
    return {'created_profiles': created_profiles, 'created_links': created_links, 'existing_links': existing_links}
