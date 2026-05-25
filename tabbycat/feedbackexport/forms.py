from collections import defaultdict

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import (
    FeedbackExportPermission,
    GlobalFeedbackExportPermission,
)


class FeedbackExportAccessForm(forms.Form):
    user = forms.ModelChoiceField(queryset=get_user_model().objects.order_by('username'), label=_('User'))
    permissions = forms.MultipleChoiceField(
        choices=FeedbackExportPermission.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_('Permissions'),
    )

    def save(self):
        user = self.cleaned_data['user']
        permissions = set(self.cleaned_data['permissions'])
        if FeedbackExportPermission.MANAGE in permissions:
            permissions.add(FeedbackExportPermission.VIEW)
        GlobalFeedbackExportPermission.objects.filter(user=user).delete()
        GlobalFeedbackExportPermission.objects.bulk_create([
            GlobalFeedbackExportPermission(user=user, permission=permission)
            for permission in sorted(permissions)
        ])
        return user


class FeedbackExportFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', _('All statuses'))] + [
            ('pending', _('Pending')),
            ('sent', _('Sent')),
            ('failed', _('Failed')),
            ('permanent_failed', _('Permanently failed')),
        ],
        required=False,
    )


def access_rows():
    rows = defaultdict(list)
    for permission in GlobalFeedbackExportPermission.objects.select_related('user').order_by('user__username', 'permission'):
        rows[permission.user].append(permission.permission)
    return rows.items()
