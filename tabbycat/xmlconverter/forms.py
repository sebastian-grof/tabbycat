from django import forms
from django.utils.translation import gettext_lazy as _


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
