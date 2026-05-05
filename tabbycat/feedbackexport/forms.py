from collections import defaultdict

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from participants.models import Adjudicator

from .models import (
    FeedbackExportPermission,
    GlobalFeedbackExportPermission,
    JudgeProfile,
    JudgeProfileLink,
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


class JudgeProfileForm(forms.ModelForm):
    extra_emails_text = forms.CharField(
        label=_('Extra emails'), required=False, widget=forms.Textarea(attrs={'rows': 2}),
        help_text=_('One email per line.'),
    )

    class Meta:
        model = JudgeProfile
        fields = ['name', 'primary_email', 'external_id', 'extra_emails_text', 'active', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['extra_emails_text'].initial = '\n'.join(self.instance.extra_emails or [])

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.primary_email = profile.primary_email or None
        profile.external_id = profile.external_id or None
        profile.extra_emails = [
            line.strip() for line in self.cleaned_data.get('extra_emails_text', '').splitlines() if line.strip()
        ]
        if commit:
            profile.save()
        return profile


class JudgeProfileLinkForm(forms.ModelForm):
    class Meta:
        model = JudgeProfileLink
        fields = ['profile', 'adjudicator']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile'].queryset = JudgeProfile.objects.order_by('name')
        self.fields['adjudicator'].queryset = Adjudicator.objects.select_related('tournament', 'institution').filter(
            judge_profile_link__isnull=True,
        ).order_by('name', 'tournament__name')


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
