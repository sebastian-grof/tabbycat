from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class XmlConverterConfig(AppConfig):
    name = 'xmlconverter'
    verbose_name = _('XML converter')
