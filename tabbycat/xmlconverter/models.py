from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.models import UniqueConstraint


class ConverterPermission(models.TextChoices):
    USE = 'use.converter', _('use converter')


class GlobalConverterPermission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, verbose_name=_("user"))
    permission = models.CharField(max_length=50, choices=ConverterPermission.choices, verbose_name=_("permission"))

    class Meta:
        constraints = [UniqueConstraint(fields=['user', 'permission'])]
        verbose_name = _('global converter permission')
        verbose_name_plural = _('global converter permissions')

    def __str__(self):
        return "%s: %s" % (self.user, self.permission)
