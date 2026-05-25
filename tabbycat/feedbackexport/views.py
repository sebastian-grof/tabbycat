from collections import Counter

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic import RedirectView, TemplateView

from adjfeedback.models import AdjudicatorFeedback
from tournaments.models import Tournament

from .forms import FeedbackExportAccessForm, FeedbackExportFilterForm, access_rows
from .models import (
    AdjudicatorStatsExportEvent,
    FeedbackExportEvent,
    FeedbackExportPermission,
)
from .permissions import can_manage_feedback_export, has_feedback_export_permission
from .services import (
    adjudicator_stats_event_needs_reexport,
    adjudicator_stats_export_enabled,
    adjudicator_stats_export_endpoint,
    queue_adjudicator_stats_export,
    queue_confirmed_feedback,
    queue_feedback_export,
    send_pending_adjudicator_stats_events,
    send_pending_events,
)


class FeedbackExportPermissionMixin(UserPassesTestMixin):
    required_permission = FeedbackExportPermission.VIEW
    page_emoji = '🧭'
    page_title = gettext_lazy('API Exports')

    def test_func(self):
        return has_feedback_export_permission(self.request.user, self.required_permission)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('page_title', self.page_title)
        kwargs.setdefault('page_emoji', self.page_emoji)
        kwargs['can_manage_feedback_export'] = can_manage_feedback_export(self.request.user)
        kwargs['feedback_export_nav'] = True
        kwargs['export_tabs'] = self.export_tabs()
        kwargs['export_enabled'] = bool(getattr(settings, 'FEEDBACK_EXPORT_ENABLED', False))
        kwargs['endpoint_configured'] = bool(getattr(settings, 'FEEDBACK_EXPORT_ENDPOINT', ''))
        kwargs['activity_export_enabled'] = adjudicator_stats_export_enabled()
        kwargs['activity_endpoint_configured'] = bool(adjudicator_stats_export_endpoint())
        return super().get_context_data(**kwargs)

    def export_tabs(self):
        return [
            (_('Overview'), reverse('feedbackexport-index'), 'dashboard'),
            (_('Judge Data'), reverse('feedbackexport-events'), 'judge_data'),
            (_('Access'), reverse('feedbackexport-access'), 'access'),
        ]


class FeedbackExportManageMixin(FeedbackExportPermissionMixin):
    required_permission = FeedbackExportPermission.MANAGE


def confirmed_feedback_queryset():
    return AdjudicatorFeedback.objects.filter(confirmed=True)


def event_status_count_map(model):
    return Counter(dict(model.objects.values_list('status').annotate(count=Count('id'))))


class FeedbackExportIndexView(FeedbackExportPermissionMixin, TemplateView):
    template_name = 'feedbackexport/index.html'

    def get_context_data(self, **kwargs):
        status_counts = event_status_count_map(FeedbackExportEvent)
        activity_status_counts = event_status_count_map(AdjudicatorStatsExportEvent)
        kwargs['active_tab'] = 'dashboard'
        kwargs['status_counts'] = status_counts
        kwargs['activity_status_counts'] = activity_status_counts
        kwargs['confirmed_feedback_count'] = confirmed_feedback_queryset().count()
        kwargs['activity_event_count'] = AdjudicatorStatsExportEvent.objects.count()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not can_manage_feedback_export(request.user):
            return self.handle_no_permission()
        action = request.POST.get('action')
        if action == 'queue_all':
            result = queue_confirmed_feedback(force=True, reset_attempts=True)
            messages.success(request, _('%(queued)s feedback export events queued; %(skipped)s skipped.') % result)
        elif action == 'send_pending':
            result = send_pending_events(limit=100)
            messages.success(request, _('%(processed)s export events processed; %(sent)s sent; %(failed)s failed.') % result)
        return redirect('feedbackexport-index')


class FeedbackExportProfilesRedirectView(FeedbackExportPermissionMixin, RedirectView):
    pattern_name = 'feedbackexport-index'
    permanent = False


class JudgeDataExportView(FeedbackExportPermissionMixin, TemplateView):
    template_name = 'feedbackexport/events.html'

    def get_context_data(self, **kwargs):
        filter_form = kwargs.get('filter_form') or FeedbackExportFilterForm(self.request.GET or None)
        events = FeedbackExportEvent.objects.select_related(
            'feedback', 'feedback__adjudicator', 'feedback__adjudicator__tournament',
        ).order_by('-updated_at')
        if filter_form.is_valid() and filter_form.cleaned_data.get('status'):
            events = events.filter(status=filter_form.cleaned_data['status'])
        tournaments = Tournament.objects.order_by('-active', 'seq', 'name').prefetch_related(
            'break_tournaments__season__league',
            'break_tournaments__region',
        )
        activity_events = {
            event.source_tournament_id: event
            for event in AdjudicatorStatsExportEvent.objects.select_related('tournament', 'break_tournament').all()
            if event.source_tournament_id is not None
        }
        activity_rows = []
        for tournament in tournaments:
            event = activity_events.get(tournament.id)
            break_tournament = next(iter(tournament.break_tournaments.all()), None)
            activity_rows.append({
                'tournament': tournament,
                'event': event,
                'break_tournament': break_tournament,
                'status': _activity_status(event, tournament),
            })

        kwargs['active_tab'] = 'judge_data'
        kwargs['filter_form'] = filter_form
        kwargs['events'] = events[:250]
        kwargs['activity_rows'] = activity_rows
        kwargs['events_without_tournament'] = AdjudicatorStatsExportEvent.objects.filter(
            tournament__isnull=True,
            source_tournament_id__isnull=False,
        ).order_by('-updated_at')[:50]
        kwargs['status_counts'] = event_status_count_map(FeedbackExportEvent)
        kwargs['activity_status_counts'] = event_status_count_map(AdjudicatorStatsExportEvent)
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not can_manage_feedback_export(request.user):
            return self.handle_no_permission()
        action = request.POST.get('action')
        redirect_name = request.resolver_match.url_name or 'feedbackexport-events'
        if action in {'retry_event', 'retry_feedback_event'}:
            event = get_object_or_404(FeedbackExportEvent, id=request.POST.get('event_id'))
            queue_feedback_export(event.feedback, force=True, reset_attempts=True)
            messages.success(request, _('Feedback export event was queued for retry.'))
        elif action in {'retry_failed_feedback', 'retry_failed'}:
            count = 0
            for event in FeedbackExportEvent.objects.filter(
                status__in=[FeedbackExportEvent.Status.FAILED, FeedbackExportEvent.Status.PERMANENT_FAILED]
            ).select_related('feedback'):
                queue_feedback_export(event.feedback, force=True, reset_attempts=True)
                count += 1
            messages.success(request, _('%(count)s failed export events were queued for retry.') % {'count': count})
        elif action in {'send_pending_feedback', 'send_pending'} and redirect_name != 'feedbackexport-activity':
            result = send_pending_events(limit=100)
            messages.success(request, _('%(processed)s export events processed; %(sent)s sent; %(failed)s failed.') % result)
        elif action in {'queue_feedback', 'queue_all'}:
            result = queue_confirmed_feedback(force=True, reset_attempts=True)
            messages.success(request, _('%(queued)s feedback export events queued; %(skipped)s skipped.') % result)
        elif action in {'queue_activity_selected', 'force_activity_selected', 'queue_selected', 'force_selected'}:
            ids = _selected_tournament_ids(request)
            tournaments = Tournament.objects.filter(id__in=ids)
            queued = 0
            for tournament in tournaments:
                queue_adjudicator_stats_export(
                    tournament,
                    force=action in {'force_activity_selected', 'force_selected'},
                    reset_attempts=True,
                )
                queued += 1
            messages.success(request, _('%(queued)s judge activity export events queued.') % {'queued': queued})
        elif action in {'retry_failed_activity'} or (action == 'retry_failed' and redirect_name == 'feedbackexport-activity'):
            queued = 0
            for event in AdjudicatorStatsExportEvent.objects.filter(
                status__in=[
                    AdjudicatorStatsExportEvent.Status.FAILED,
                    AdjudicatorStatsExportEvent.Status.PERMANENT_FAILED,
                ],
            ).select_related('tournament'):
                if event.tournament_id:
                    queue_adjudicator_stats_export(event.tournament, force=True, reset_attempts=True)
                elif event.payload:
                    event.status = AdjudicatorStatsExportEvent.Status.PENDING
                    event.attempts = 0
                    event.next_attempt_at = timezone.now()
                    event.last_error = ''
                    event.save(update_fields=['status', 'attempts', 'next_attempt_at', 'last_error', 'updated_at'])
                else:
                    continue
                queued += 1
            messages.success(request, _('%(queued)s failed judge activity events queued for retry.') % {'queued': queued})
        elif action in {'send_pending_activity'} or (action == 'send_pending' and redirect_name == 'feedbackexport-activity'):
            result = send_pending_adjudicator_stats_events(limit=100)
            messages.success(request, _('%(processed)s judge activity events processed; %(sent)s sent; %(failed)s failed.') % result)
        return redirect(redirect_name)


def _activity_status(event, tournament):
    if event is None:
        return {
            'key': 'not_exported',
            'label': _('Not exported'),
            'badge': 'secondary',
        }
    if adjudicator_stats_event_needs_reexport(event, tournament):
        return {
            'key': 'needs_reexport',
            'label': _('Needs re-export'),
            'badge': 'warning',
        }
    return {
        'key': event.status,
        'label': event.get_status_display(),
        'badge': {
            AdjudicatorStatsExportEvent.Status.PENDING: 'info',
            AdjudicatorStatsExportEvent.Status.SENT: 'success',
            AdjudicatorStatsExportEvent.Status.FAILED: 'warning',
            AdjudicatorStatsExportEvent.Status.PERMANENT_FAILED: 'danger',
        }.get(event.status, 'secondary'),
    }


def _selected_tournament_ids(request):
    ids = []
    for value in request.POST.getlist('tournaments'):
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            continue
    return ids


class FeedbackExportAccessView(FeedbackExportManageMixin, TemplateView):
    template_name = 'feedbackexport/access.html'

    def get_context_data(self, **kwargs):
        kwargs['active_tab'] = 'access'
        kwargs['form'] = kwargs.get('form') or FeedbackExportAccessForm()
        kwargs['access_rows'] = access_rows()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        form = FeedbackExportAccessForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _('API export access updated for %(user)s.') % {'user': user})
            return redirect('feedbackexport-access')
        return self.render_to_response(self.get_context_data(form=form))
