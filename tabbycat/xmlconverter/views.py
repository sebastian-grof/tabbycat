import logging
from pathlib import Path
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.text import slugify
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import ConverterAccessForm, ConverterUploadForm
from .models import GlobalConverterPermission
from .permissions import can_manage_converter_access, can_use_converter
from .styled import convert_debatexml_to_xlsx_bytes

logger = logging.getLogger(__name__)


class ConverterView(UserPassesTestMixin, FormView):
    template_name = 'xmlconverter/index.html'
    form_class = ConverterUploadForm
    page_emoji = '↔'
    page_title = gettext_lazy('Converter')

    def test_func(self):
        return can_use_converter(self.request.user)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('page_title', self.page_title)
        kwargs.setdefault('page_emoji', self.page_emoji)
        kwargs.setdefault('can_manage_converter_access', can_manage_converter_access(self.request.user))
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        uploaded = form.cleaned_data['xml_file']
        uploaded.seek(0)
        try:
            workbook = convert_debatexml_to_xlsx_bytes(uploaded, source_name=uploaded.name)
        except Exception:
            logger.exception('Failed to convert DebateXML upload')
            form.add_error('xml_file', _(
                "This file could not be converted. Please make sure it is a valid Tabbycat DebateXML export."
            ))
            return self.form_invalid(form)

        stem = slugify(Path(uploaded.name).stem) or 'results'
        response = HttpResponse(
            workbook,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="%s.xlsx"' % stem
        return response


class ConverterAccessView(UserPassesTestMixin, TemplateView):
    template_name = 'xmlconverter/access.html'
    page_emoji = '↔'
    page_title = gettext_lazy('Converter access')

    def test_func(self):
        return can_manage_converter_access(self.request.user)

    def get_context_data(self, **kwargs):
        permissions_by_user = defaultdict(list)
        for permission in GlobalConverterPermission.objects.select_related('user').order_by('user__username', 'permission'):
            permissions_by_user[permission.user].append(permission.permission)
        kwargs.setdefault('page_title', self.page_title)
        kwargs.setdefault('page_emoji', self.page_emoji)
        kwargs['form'] = kwargs.get('form') or ConverterAccessForm()
        kwargs['access_rows'] = permissions_by_user.items()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        form = ConverterAccessForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Converter access updated for %(user)s.") % {'user': user})
            return redirect('xmlconverter-access')
        return self.render_to_response(self.get_context_data(form=form))
