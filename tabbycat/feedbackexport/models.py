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

    feedback = models.OneToOneField('adjfeedback.AdjudicatorFeedback', models.CASCADE, related_name='export_event',
        verbose_name=_('feedback'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True,
        verbose_name=_('status'))
    idempotency_key = models.CharField(max_length=120, unique=True, verbose_name=_('idempotency key'))
    attempts = models.PositiveSmallIntegerField(default=0, verbose_name=_('attempts'))
    next_attempt_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=_('next attempt at'))
    last_error = models.TextField(blank=True, verbose_name=_('last error'))
    last_http_status = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('last HTTP status'))
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
        return "%s feedback #%s" % (self.status, self.feedback_id)

    @property
    def can_retry(self):
        return self.status in {self.Status.PENDING, self.Status.FAILED, self.Status.PERMANENT_FAILED}

    def mark_sent(self, response_data=None, http_status=None):
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.last_error = ''
        self.last_http_status = http_status
        self.remote_response = response_data
        self.save(update_fields=['status', 'sent_at', 'last_error', 'last_http_status', 'remote_response', 'updated_at'])

    def mark_failed(self, error, *, permanent=False, http_status=None, retry_at=None):
        self.status = self.Status.PERMANENT_FAILED if permanent else self.Status.FAILED
        self.last_error = str(error)
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
    break_tournament = models.OneToOneField('seasonbreaks.BreakTournament', models.SET_NULL, blank=True, null=True,
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
        self.remote_response = response_data
        self.save(update_fields=['status', 'sent_at', 'last_error', 'last_http_status', 'remote_response', 'updated_at'])

    def mark_failed(self, error, *, permanent=False, http_status=None, retry_at=None):
        self.status = self.Status.PERMANENT_FAILED if permanent else self.Status.FAILED
        self.last_error = str(error)
        self.last_http_status = http_status
        self.next_attempt_at = None if permanent else retry_at
        self.save(update_fields=['status', 'last_error', 'last_http_status', 'next_attempt_at', 'updated_at'])
