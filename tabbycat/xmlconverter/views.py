import logging
from pathlib import Path

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.utils.text import slugify
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic.edit import FormView

from .forms import ConverterUploadForm
from .permissions import has_converter_permission
from .styled import convert_debatexml_to_xlsx_bytes

logger = logging.getLogger(__name__)


class ConverterView(UserPassesTestMixin, FormView):
    template_name = 'xmlconverter/index.html'
    form_class = ConverterUploadForm
    page_emoji = '↔'
    page_title = gettext_lazy('Converter')

    def test_func(self):
        return has_converter_permission(self.request.user)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('page_title', self.page_title)
        kwargs.setdefault('page_emoji', self.page_emoji)
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
