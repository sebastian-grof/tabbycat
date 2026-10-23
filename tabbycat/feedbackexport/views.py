import json
import uuid

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _, gettext_lazy
from django.views import View
from django.views.generic import RedirectView, TemplateView

from adjfeedback.models import AdjudicatorFeedback
from tournaments.models import Tournament

from .forms import access_rows, FeedbackExportAccessForm
from .jobs import configuration, control_job, create_backlog_job, create_job, job_summary
from .models import AdjudicatorStatsExportEvent, ExportJob, ExportJobItem, FeedbackExportEvent, FeedbackExportPermission
from .permissions import can_manage_feedback_export, has_feedback_export_permission


class FeedbackExportPermissionMixin(UserPassesTestMixin):
    required_permission = FeedbackExportPermission.VIEW
    page_emoji = '↗'
    page_title = gettext_lazy('DR exports')

    def test_func(self):
        return has_feedback_export_permission(self.request.user, self.required_permission)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('page_title', self.page_title)
        kwargs.setdefault('page_emoji', self.page_emoji)
        kwargs['can_manage_feedback_export'] = can_manage_feedback_export(self.request.user)
        kwargs['feedback_export_nav'] = True
        kwargs['health'] = configuration()
        kwargs['export_tabs'] = [
            (_('Export'), reverse('feedbackexport-index'), 'export'),
            (_('History'), reverse('feedbackexport-history'), 'history'),
            (_('Access'), reverse('feedbackexport-access'), 'access'),
        ]
        return super().get_context_data(**kwargs)


class FeedbackExportManageMixin(FeedbackExportPermissionMixin):
    required_permission = FeedbackExportPermission.MANAGE


class FeedbackExportIndexView(FeedbackExportPermissionMixin, TemplateView):
    template_name = 'feedbackexport/index.html'

    def get_context_data(self, **kwargs):
        counts = dict(AdjudicatorFeedback.objects.filter(confirmed=True).values_list(
            'adjudicator__tournament_id',
        ).annotate(n=Count('id')))
        tournaments = list(Tournament.objects.order_by('-active', 'seq', 'name'))
        for tournament in tournaments:
            tournament.export_feedback_count = counts.get(tournament.id, 0)
        kwargs.update(
            active_tab='export', tournaments=tournaments, submission_token=str(uuid.uuid4()), backlog_token=str(uuid.uuid4()),
            latest_job=ExportJob.objects.order_by('-id').first(),
            active_job=ExportJob.objects.exclude(status__in=['completed', 'completed_errors']).order_by('id').first(),
            backlog_count=(FeedbackExportEvent.objects.exclude(status='sent').filter(job_items__isnull=True).count() +
                           AdjudicatorStatsExportEvent.objects.exclude(status='sent').filter(job_items__isnull=True).count()),
        )
        return super().get_context_data(**kwargs)


class LegacyExportRedirectView(FeedbackExportPermissionMixin, RedirectView):
    pattern_name = 'feedbackexport-index'
    permanent = False

    def post(self, request, *args, **kwargs):
        # Old forms must never send data or silently change the new manual scope.
        return redirect(self.pattern_name)


FeedbackExportProfilesRedirectView = LegacyExportRedirectView
JudgeDataExportView = LegacyExportRedirectView


class ExportHistoryView(FeedbackExportPermissionMixin, TemplateView):
    template_name = 'feedbackexport/history.html'

    def get_context_data(self, **kwargs):
        jobs = ExportJob.objects.select_related('requested_by').order_by('-id')
        filters = {}
        tournament_id = self.request.GET.get('tournament', '')
        if tournament_id.isdigit():
            filters['items__tournament_id'] = int(tournament_id)
        kind = self.request.GET.get('kind', '')
        if kind in {'feedback', 'activity'}:
            jobs = jobs.filter(export_types__contains=[kind])
        status = self.request.GET.get('status', '')
        if status in ExportJob.Status.values:
            jobs = jobs.filter(status=status)
        if filters:
            jobs = jobs.filter(pk__in=ExportJob.objects.filter(**filters).values('pk'))
        jobs = jobs.annotate(
            total=Count('items', distinct=True),
            sent=Count('items', filter=Q(items__status='sent'), distinct=True),
            failed=Count('items', filter=Q(items__status='failed'), distinct=True),
            unchanged=Count('items', filter=Q(items__status='unchanged'), distinct=True),
        )
        page = Paginator(jobs, 25).get_page(self.request.GET.get('page'))
        query = self.request.GET.copy()
        query.pop('page', None)
        kwargs.update(active_tab='history', page=page, filter_query=query.urlencode(),
                      statuses=ExportJob.Status.choices, selected_status=status, selected_kind=kind,
                      selected_tournament=tournament_id, tournaments=Tournament.objects.order_by('name'))
        return super().get_context_data(**kwargs)


class ExportJobView(FeedbackExportPermissionMixin, TemplateView):
    template_name = 'feedbackexport/job.html'

    def get_context_data(self, **kwargs):
        job = get_object_or_404(ExportJob.objects.select_related('requested_by'), pk=self.kwargs['pk'])
        items = job.items.all()
        status = self.request.GET.get('status', '')
        if status in ExportJobItem.Status.values:
            items = items.filter(status=status)
        kwargs.update(active_tab='export', job=job, summary=job_summary(job),
                      items_page=Paginator(items, 50).get_page(self.request.GET.get('page')),
                      item_statuses=ExportJobItem.Status.choices, selected_status=status)
        return super().get_context_data(**kwargs)


class ExportJobCreateView(FeedbackExportManageMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else {
                'tournament_ids': request.POST.getlist('tournaments'),
                'export_types': [request.POST.get('kind', 'feedback')],
                'force': request.POST.get('force') == 'on',
                'submission_token': request.POST.get('submission_token'),
                'backlog': request.POST.get('backlog') == '1',
            }
            if not isinstance(data, dict) or not data.get('submission_token'):
                raise ValueError('A submission token is required. Refresh the page and try again.')
            if type(data.get('force', False)) is not bool or type(data.get('backlog', False)) is not bool:
                raise ValueError('Invalid export options.')
            common = {'requested_by': request.user, 'submission_token': data['submission_token']}
            if data.get('backlog'):
                job = create_backlog_job(**common)
            else:
                kinds = data.get('export_types', [])
                if kinds == ['both']:
                    kinds = ['feedback', 'activity']
                if not isinstance(kinds, list) or not isinstance(data.get('tournament_ids'), list):
                    raise ValueError('Select tournaments and export types.')
                job = create_job(tournament_ids=data['tournament_ids'], kinds=kinds, force=data.get('force', False), **common)
        except (ValueError, TypeError, AttributeError) as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        url = reverse('feedbackexport-job', args=[job.id])
        if request.content_type != 'application/json' and request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return redirect(url)
        response = JsonResponse({'id': job.id, 'url': url, 'status_url': reverse('feedbackexport-job-status', args=[job.id])}, status=202)
        response['Location'] = url
        return response


class ExportJobStatusView(FeedbackExportPermissionMixin, View):
    def get(self, request, pk):
        job = get_object_or_404(ExportJob, pk=pk)
        response = JsonResponse({**job_summary(job), 'health': configuration()})
        response['Cache-Control'] = 'no-store'
        return response


class ExportJobItemsView(FeedbackExportPermissionMixin, View):
    def get(self, request, pk):
        job = get_object_or_404(ExportJob, pk=pk)
        items = job.items.all()
        status = request.GET.get('status')
        if status in ExportJobItem.Status.values:
            items = items.filter(status=status)
        page = Paginator(items.values('id', 'kind', 'source_id', 'tournament_id', 'label', 'status',
                                     'attempts', 'next_attempt_at', 'last_error', 'http_status', 'receipt', 'updated_at'), 50).get_page(request.GET.get('page'))
        response = JsonResponse({'items': list(page), 'page': page.number, 'pages': page.paginator.num_pages})
        response['Cache-Control'] = 'no-store'
        return response


class ExportJobControlView(FeedbackExportManageMixin, View):
    def post(self, request, pk, action):
        get_object_or_404(ExportJob, pk=pk)
        try:
            job = control_job(pk, action)
        except ValueError as exc:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': str(exc)}, status=409)
            messages.error(request, str(exc))
            return redirect('feedbackexport-job', pk=pk)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(job_summary(job))
        return redirect('feedbackexport-job', pk=pk)


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
