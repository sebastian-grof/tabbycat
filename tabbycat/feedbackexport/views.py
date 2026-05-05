from collections import Counter, defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic import TemplateView

from adjfeedback.models import AdjudicatorFeedback
from participants.models import Adjudicator

from .forms import FeedbackExportAccessForm, FeedbackExportFilterForm, JudgeProfileForm, JudgeProfileLinkForm, access_rows
from .models import FeedbackExportEvent, FeedbackExportPermission, GlobalFeedbackExportPermission, JudgeProfile, JudgeProfileLink
from .permissions import can_manage_feedback_export, has_feedback_export_permission
from .services import auto_create_profiles_from_adjudicators, queue_confirmed_feedback, queue_feedback_export, send_pending_events


class FeedbackExportPermissionMixin(UserPassesTestMixin):
    required_permission = FeedbackExportPermission.VIEW
    page_emoji = '🧭'
    page_title = gettext_lazy('Feedback Export')

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
        return super().get_context_data(**kwargs)

    def export_tabs(self):
        return [
            (_('Dashboard'), reverse('feedbackexport-index'), 'dashboard'),
            (_('Judge Profiles'), reverse('feedbackexport-profiles'), 'profiles'),
            (_('Export Events'), reverse('feedbackexport-events'), 'events'),
            (_('Access'), reverse('feedbackexport-access'), 'access'),
        ]


class FeedbackExportManageMixin(FeedbackExportPermissionMixin):
    required_permission = FeedbackExportPermission.MANAGE


def confirmed_feedback_queryset():
    return AdjudicatorFeedback.objects.filter(confirmed=True)


def unmapped_target_adjudicators():
    return Adjudicator.objects.filter(
        adjudicatorfeedback__confirmed=True,
        judge_profile_link__isnull=True,
    ).select_related('tournament', 'institution').distinct().order_by('name')


class FeedbackExportIndexView(FeedbackExportPermissionMixin, TemplateView):
    template_name = 'feedbackexport/index.html'

    def get_context_data(self, **kwargs):
        status_counts = Counter(dict(
            FeedbackExportEvent.objects.values_list('status').annotate(count=Count('id'))
        ))
        kwargs['active_tab'] = 'dashboard'
        kwargs['status_counts'] = status_counts
        kwargs['confirmed_feedback_count'] = confirmed_feedback_queryset().count()
        kwargs['profile_count'] = JudgeProfile.objects.count()
        kwargs['linked_adjudicator_count'] = JudgeProfileLink.objects.count()
        kwargs['unmapped_targets'] = unmapped_target_adjudicators()[:25]
        kwargs['unmapped_target_count'] = unmapped_target_adjudicators().count()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not can_manage_feedback_export(request.user):
            return self.handle_no_permission()
        action = request.POST.get('action')
        if action == 'queue_all':
            result = queue_confirmed_feedback(force=True, reset_attempts=True)
            messages.success(request, _('%(queued)s feedback export events queued; %(blocked)s blocked by missing judge profile.') % result)
        elif action == 'send_pending':
            result = send_pending_events(limit=100)
            messages.success(request, _('%(processed)s export events processed; %(sent)s sent; %(failed)s failed.') % result)
        elif action == 'auto_profiles':
            result = auto_create_profiles_from_adjudicators(unmapped_target_adjudicators())
            messages.success(request, _('%(created_profiles)s judge profiles and %(created_links)s links created.') % result)
        return redirect('feedbackexport-index')


class FeedbackExportProfilesView(FeedbackExportPermissionMixin, TemplateView):
    template_name = 'feedbackexport/profiles.html'

    def get_context_data(self, **kwargs):
        kwargs['active_tab'] = 'profiles'
        kwargs['profiles'] = JudgeProfile.objects.prefetch_related('links__adjudicator__tournament').all()
        kwargs['profile_form'] = kwargs.get('profile_form') or JudgeProfileForm()
        kwargs['link_form'] = kwargs.get('link_form') or JudgeProfileLinkForm()
        kwargs['unmapped_targets'] = unmapped_target_adjudicators()[:50]
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not can_manage_feedback_export(request.user):
            return self.handle_no_permission()
        action = request.POST.get('action')
        if action == 'create_profile':
            form = JudgeProfileForm(request.POST)
            if form.is_valid():
                profile = form.save()
                messages.success(request, _('Judge profile %(profile)s was created.') % {'profile': profile})
                return redirect('feedbackexport-profiles')
            return self.render_to_response(self.get_context_data(profile_form=form))
        if action == 'create_link':
            form = JudgeProfileLinkForm(request.POST)
            if form.is_valid():
                link = form.save()
                messages.success(request, _('Linked %(adjudicator)s to %(profile)s.') % {
                    'adjudicator': link.adjudicator, 'profile': link.profile,
                })
                return redirect('feedbackexport-profiles')
            return self.render_to_response(self.get_context_data(link_form=form))
        if action == 'auto_profiles':
            result = auto_create_profiles_from_adjudicators(unmapped_target_adjudicators())
            messages.success(request, _('%(created_profiles)s judge profiles and %(created_links)s links created.') % result)
            return redirect('feedbackexport-profiles')
        return redirect('feedbackexport-profiles')


class FeedbackExportEventsView(FeedbackExportPermissionMixin, TemplateView):
    template_name = 'feedbackexport/events.html'

    def get_context_data(self, **kwargs):
        filter_form = kwargs.get('filter_form') or FeedbackExportFilterForm(self.request.GET or None)
        events = FeedbackExportEvent.objects.select_related(
            'feedback', 'feedback__adjudicator', 'feedback__adjudicator__tournament',
        ).order_by('-updated_at')
        if filter_form.is_valid() and filter_form.cleaned_data.get('status'):
            events = events.filter(status=filter_form.cleaned_data['status'])
        kwargs['active_tab'] = 'events'
        kwargs['filter_form'] = filter_form
        kwargs['events'] = events[:250]
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not can_manage_feedback_export(request.user):
            return self.handle_no_permission()
        action = request.POST.get('action')
        if action == 'retry_event':
            event = get_object_or_404(FeedbackExportEvent, id=request.POST.get('event_id'))
            queue_feedback_export(event.feedback, force=True, reset_attempts=True)
            messages.success(request, _('Feedback export event was queued for retry.'))
        elif action == 'retry_failed':
            count = 0
            for event in FeedbackExportEvent.objects.filter(
                status__in=[FeedbackExportEvent.Status.FAILED, FeedbackExportEvent.Status.PERMANENT_FAILED]
            ).select_related('feedback'):
                queue_feedback_export(event.feedback, force=True, reset_attempts=True)
                count += 1
            messages.success(request, _('%(count)s failed export events were queued for retry.') % {'count': count})
        elif action == 'send_pending':
            result = send_pending_events(limit=100)
            messages.success(request, _('%(processed)s export events processed; %(sent)s sent; %(failed)s failed.') % result)
        elif action == 'queue_all':
            result = queue_confirmed_feedback(force=True, reset_attempts=True)
            messages.success(request, _('%(queued)s feedback export events queued; %(blocked)s blocked by missing judge profile.') % result)
        return redirect('feedbackexport-events')


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
            messages.success(request, _('Feedback export access updated for %(user)s.') % {'user': user})
            return redirect('feedbackexport-access')
        return self.render_to_response(self.get_context_data(form=form))
