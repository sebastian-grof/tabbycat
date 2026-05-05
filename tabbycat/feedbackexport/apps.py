from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FeedbackExportConfig(AppConfig):
    name = 'feedbackexport'
    verbose_name = _('Feedback Export')

    def ready(self):
        from . import signals  # noqa: F401
