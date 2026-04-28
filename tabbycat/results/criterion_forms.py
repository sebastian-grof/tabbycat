from django import forms
from django.forms import formset_factory
from django.utils.translation import gettext_lazy as _

from .models import CriterionPreset


class CriterionEntryForm(forms.Form):
    item_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    order = forms.IntegerField(label=_("Order"), min_value=1, required=False)
    name = forms.CharField(label=_("Name"), max_length=40, required=False)
    weight = forms.FloatField(label=_("Weight"), min_value=0, required=False)
    min_score = forms.FloatField(label=_("Minimum"), required=False)
    max_score = forms.FloatField(label=_("Maximum"), required=False)
    step = forms.FloatField(label=_("Step"), min_value=0.000001, required=False)
    required = forms.BooleanField(label=_("Required"), required=False)
    delete = forms.BooleanField(label=_("Delete"), required=False)

    name_max_length = 40

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].max_length = self.name_max_length
        self.fields['name'].widget.attrs['maxlength'] = self.name_max_length

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('delete'):
            return cleaned_data

        has_value = any(
            cleaned_data.get(field) not in (None, '', False)
            for field in ('item_id', 'order', 'name', 'weight', 'min_score', 'max_score', 'step')
        )
        if not has_value:
            cleaned_data['is_blank'] = True
            return cleaned_data

        for field in ('order', 'name', 'weight', 'min_score', 'max_score', 'step'):
            if cleaned_data.get(field) in (None, ''):
                self.add_error(field, forms.ValidationError(_("This field is required.")))

        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        if min_score is not None and max_score is not None and max_score < min_score:
            self.add_error('max_score', forms.ValidationError(_("Maximum must be at least the minimum.")))

        return cleaned_data

    def entry(self):
        if self.cleaned_data.get('is_blank'):
            return None
        return {
            'id': self.cleaned_data.get('item_id'),
            'order': self.cleaned_data.get('order'),
            'name': self.cleaned_data.get('name'),
            'weight': self.cleaned_data.get('weight'),
            'min_score': self.cleaned_data.get('min_score'),
            'max_score': self.cleaned_data.get('max_score'),
            'step': self.cleaned_data.get('step'),
            'required': self.cleaned_data.get('required'),
            'delete': self.cleaned_data.get('delete'),
        }


class ScoreCriterionEntryForm(CriterionEntryForm):
    name_max_length = 20


class CrossCriterionEntryForm(CriterionEntryForm):
    name_max_length = 40


ScoreCriterionFormSet = formset_factory(ScoreCriterionEntryForm, extra=0)
CrossCriterionFormSet = formset_factory(CrossCriterionEntryForm, extra=0)


class ApplyCriterionPresetForm(forms.Form):
    preset = forms.ModelChoiceField(
        queryset=CriterionPreset.objects.none(),
        label=_("Preset"),
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preset'].queryset = CriterionPreset.objects.order_by('-builtin', 'name')


class SaveCriterionPresetForm(forms.Form):
    name = forms.CharField(max_length=100, label=_("Preset name"))
    description = forms.CharField(
        label=_("Description"),
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if CriterionPreset.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError(_("A preset with this name already exists."))
        return name


class DeleteCriterionPresetForm(forms.Form):
    preset_id = forms.ModelChoiceField(
        queryset=CriterionPreset.objects.none(),
        label=_("Preset to remove"),
        empty_label=_("Choose a preset"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preset_id'].queryset = CriterionPreset.objects.filter(builtin=False)
