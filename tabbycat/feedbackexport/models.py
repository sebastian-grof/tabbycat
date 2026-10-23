import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from utils.models import UniqueConstraint


class FeedbackExportPermission(models.TextChoices):
    VIEW = 'view.feedback_export', _('view feedback export')
    MANAGE = 'manage.feedback_export', _('manage feedback export')


class GlobalFeedbackExportPermission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, verbose_name=_('user'))
    permission = models.CharField(max_length=50, choices=FeedbackExportPermission.choices, verbose_name=_('permission'))

    class Meta:
        constraints = [UniqueConstraint(fields=['user', 'permission'])]
        verbose_name = _('global feedback export permission')
        verbose_name_plural = _('global feedback export permissions')

    def __str__(self):
        return "%s: %s" % (self.user, self.permission)


class FeedbackExportEvent(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('pending')
        SENT = 'sent', _('sent')
        FAILED = 'failed', _('failed')
        PERMANENT_FAILED = 'permanent_failed', _('permanently failed')

    source_feedback_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    source_tournament_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    feedback = models.ForeignKey('adjfeedback.AdjudicatorFeedback', models.SET_NULL, null=True, blank=True, related_name='export_events',
        verbose_name=_('feedback'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True,
        verbose_name=_('status'))
    idempotency_key = models.CharField(max_length=120, unique=True, verbose_name=_('idempotency key'))
    attempts = models.PositiveSmallIntegerField(default=0, verbose_name=_('attempts'))
    next_attempt_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=_('next attempt at'))
    last_error = models.TextField(blank=True, verbose_name=_('last error'))
    last_http_status = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('last HTTP status'))
    receipt = models.JSONField(default=dict, blank=True)
    payload_hash = models.CharField(max_length=64, blank=True, verbose_name=_('payload hash'))
    payload = models.JSONField(blank=True, null=True, verbose_name=_('payload'))
    remote_response = models.JSONField(blank=True, null=True, verbose_name=_('remote response'))
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name=_('sent at'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    class Meta:
        ordering = ['status', '-updated_at']
        verbose_name = _('feedback export event')
        verbose_name_plural = _('feedback export events')

    def __str__(self):
        return "%s feedback #%s" % (self.status, self.source_feedback_id or self.feedback_id)

    @property
    def can_retry(self):
        return self.status in {self.Status.PENDING, self.Status.FAILED, self.Status.PERMANENT_FAILED}

    def mark_sent(self, response_data=None, http_status=None):
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.last_error = ''
        self.last_http_status = http_status
        from .services import compact_receipt
        self.receipt = compact_receipt(response_data)
        self.payload = None
        self.remote_response = None
        self.next_attempt_at = None
        self.save(update_fields=['status', 'sent_at', 'last_error', 'last_http_status', 'receipt',
                                 'payload', 'remote_response', 'next_attempt_at', 'updated_at'])

    def mark_failed(self, error, *, permanent=False, http_status=None, retry_at=None):
        self.status = self.Status.PERMANENT_FAILED if permanent else self.Status.FAILED
        self.last_error = str(error).encode('utf-8')[:2048].decode('utf-8', errors='ignore')
        self.last_http_status = http_status
        self.next_attempt_at = None if permanent else retry_at
        self.save(update_fields=['status', 'last_error', 'last_http_status', 'next_attempt_at', 'updated_at'])


class AdjudicatorStatsExportEvent(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('pending')
        SENT = 'sent', _('sent')
        FAILED = 'failed', _('failed')
        PERMANENT_FAILED = 'permanent_failed', _('permanently failed')

    tournament = models.ForeignKey('tournaments.Tournament', models.SET_NULL, blank=True, null=True,
        related_name='adjudicator_stats_export_events', verbose_name=_('tournament'))
    break_tournament = models.ForeignKey('seasonbreaks.BreakTournament', models.SET_NULL, blank=True, null=True,
        related_name='adjudicator_stats_export_event', verbose_name=_('break tournament'))
    source_tournament_id = models.PositiveIntegerField(blank=True, null=True, db_index=True,
        verbose_name=_('source tournament ID'))
    source_tournament_slug = models.SlugField(blank=True, max_length=120, verbose_name=_('source tournament slug'))
    source_tournament_name = models.CharField(blank=True, max_length=100, verbose_name=_('source tournament name'))
    source_tournament_short_name = models.CharField(blank=True, max_length=25,
        verbose_name=_('source tournament short name'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True,
        verbose_name=_('status'))
    idempotency_key = models.CharField(max_length=160, unique=True, verbose_name=_('idempotency key'))
    attempts = models.PositiveSmallIntegerField(default=0, verbose_name=_('attempts'))
    next_attempt_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=_('next attempt at'))
    last_error = models.TextField(blank=True, verbose_name=_('last error'))
    last_http_status = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('last HTTP status'))
    receipt = models.JSONField(default=dict, blank=True)
    payload_hash = models.CharField(max_length=64, blank=True, verbose_name=_('payload hash'))
    payload = models.JSONField(blank=True, null=True, verbose_name=_('payload'))
    remote_response = models.JSONField(blank=True, null=True, verbose_name=_('remote response'))
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name=_('sent at'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    class Meta:
        ordering = ['status', '-updated_at']
        verbose_name = _('adjudicator stats export event')
        verbose_name_plural = _('adjudicator stats export events')

    def __str__(self):
        return "%s adjudicator stats for %s" % (
            self.status,
            self.tournament or self.source_tournament_short_name or self.source_tournament_name or self.source_tournament_id,
        )

    @property
    def can_retry(self):
        return self.status in {self.Status.PENDING, self.Status.FAILED, self.Status.PERMANENT_FAILED}

    def mark_sent(self, response_data=None, http_status=None):
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.last_error = ''
        self.last_http_status = http_status
        from .services import compact_receipt
        self.receipt = compact_receipt(response_data)
        self.payload = None
        self.remote_response = None
        self.next_attempt_at = None
        self.save(update_fields=['status', 'sent_at', 'last_error', 'last_http_status', 'receipt',
                                 'payload', 'remote_response', 'next_attempt_at', 'updated_at'])

    def mark_failed(self, error, *, permanent=False, http_status=None, retry_at=None):
        self.status = self.Status.PERMANENT_FAILED if permanent else self.Status.FAILED
        self.last_error = str(error).encode('utf-8')[:2048].decode('utf-8', errors='ignore')
        self.last_http_status = http_status
        self.next_attempt_at = None if permanent else retry_at
        self.save(update_fields=['status', 'last_error', 'last_http_status', 'next_attempt_at', 'updated_at'])


class ExportJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'queued', _('Queued')
        PREPARING = 'preparing', _('Preparing')
        RUNNING = 'running', _('Sending')
        WAITING = 'waiting', _('Waiting for retry')
        PAUSED = 'paused', _('Paused')
        BLOCKED = 'blocked', _('Needs attention')
        COMPLETED = 'completed', _('Completed')
        COMPLETED_ERRORS = 'completed_errors', _('Completed with errors')

    submission_token = models.UUIDField(default=uuid.uuid4, unique=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, null=True, blank=True)
    tournaments = models.JSONField(default=list)  # Stable IDs and names, including deleted tournaments.
    export_types = models.JSONField(default=list)
    force = models.BooleanField(default=False)
    backlog = models.BooleanField(default=False)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.QUEUED, db_index=True)
    # Finite preparation range and cursor survive worker restarts without payload duplication.
    source_limits = models.JSONField(default=dict)
    preparation_cursor = models.JSONField(default=dict)
    preparation_done = models.BooleanField(default=False)
    blocked_types = models.JSONField(default=dict)
    last_progress_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-id']

    @property
    def terminal(self):
        return self.status in {self.Status.COMPLETED, self.Status.COMPLETED_ERRORS}


class ExportJobItem(models.Model):
    class Status(models.TextChoices):
        PREPARING = 'preparing', _('Preparing')
        READY = 'ready', _('Ready')
        SENDING = 'sending', _('Sending')
        RETRY = 'retry', _('Waiting for retry')
        BLOCKED = 'blocked', _('Needs attention')
        SENT = 'sent', _('Sent')
        UNCHANGED = 'unchanged', _('Unchanged')
        FAILED = 'failed', _('Failed')

    job = models.ForeignKey(ExportJob, models.CASCADE, related_name='items')
    kind = models.CharField(max_length=16, choices=[('feedback', _('Feedback')), ('activity', _('Judge activity'))])
    source_id = models.PositiveIntegerField()
    tournament_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    label = models.CharField(max_length=250, blank=True)
    feedback_event = models.ForeignKey(FeedbackExportEvent, models.SET_NULL, null=True, blank=True, related_name='job_items')
    activity_event = models.ForeignKey(AdjudicatorStatsExportEvent, models.SET_NULL, null=True, blank=True, related_name='job_items')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PREPARING)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    claim_token = models.UUIDField(null=True, blank=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    http_status = models.PositiveSmallIntegerField(null=True, blank=True)
    receipt = models.JSONField(default=dict, blank=True)
    prepared_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        constraints = [models.UniqueConstraint(fields=['job', 'kind', 'source_id'], name='export_job_source_unique')]
        indexes = [
            models.Index(fields=['job', 'status', 'next_attempt_at'], name='export_item_due_idx'),
            models.Index(fields=['status', 'lease_expires_at'], name='export_item_lease_idx'),
        ]

    @property
    def event(self):
        return self.feedback_event if self.kind == 'feedback' else self.activity_event


class ExportWorkerState(models.Model):
    # One installation-wide lease serializes jobs and outbound requests across processes.
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    token = models.UUIDField(null=True, blank=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    last_cleanup_at = models.DateTimeField(null=True, blank=True)
