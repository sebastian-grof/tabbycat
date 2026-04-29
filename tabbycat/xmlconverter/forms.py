from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import ConverterPermission, GlobalConverterPermission


class ConverterUploadForm(forms.Form):
    xml_file = forms.FileField(
        label=_("DebateXML file"),
        help_text=_("Upload a Tabbycat DebateXML export. The converter returns an SDA-style XLSX results workbook."),
    )

    def clean_xml_file(self):
        uploaded = self.cleaned_data['xml_file']
        if not uploaded.name.lower().endswith('.xml'):
            raise forms.ValidationError(_("Please upload an XML file."))
        return uploaded


class ConverterAccessForm(forms.Form):
    user = forms.ModelChoiceField(queryset=get_user_model().objects.order_by('username'), label=_("User"))
    permissions = forms.MultipleChoiceField(
        choices=ConverterPermission.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Permissions"),
    )

    def save(self):
        user = self.cleaned_data['user']
        permissions = set(self.cleaned_data['permissions'])
        if ConverterPermission.MANAGE_ACCESS.value in permissions:
            permissions.add(ConverterPermission.USE.value)
        GlobalConverterPermission.objects.filter(user=user).delete()
        GlobalConverterPermission.objects.bulk_create([
            GlobalConverterPermission(user=user, permission=permission)
            for permission in sorted(permissions)
        ])
        return user
