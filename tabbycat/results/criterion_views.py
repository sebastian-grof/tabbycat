from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from tournaments.mixins import TournamentMixin
from users.permissions import Permission
from utils.misc import reverse_tournament
from utils.mixins import AdministratorMixin

from .criterion_forms import (
    ApplyCriterionPresetForm, CrossCriterionFormSet, DeleteCriterionPresetForm,
    SaveCriterionPresetForm, ScoreCriterionFormSet,
)
from .criterion_utils import (
    apply_preset_to_tournament, create_preset_from_tournament, save_tournament_criteria,
)
from .models import BallotSubmission, CriterionPreset, CrossExamination, ScoreCriterion


class CriterionManagementView(AdministratorMixin, TournamentMixin, TemplateView):
    template_name = "criterion_management.html"
    page_title = _("Criterion Management")
    page_emoji = '🧮'
    view_permission = Permission.VIEW_SETTINGS
    edit_permission = Permission.EDIT_SETTINGS

    def get_success_url(self):
        return reverse_tournament('criterion-management', self.tournament)

    def get_substantive_initial(self):
        criteria = ScoreCriterion.objects.filter(
            tournament=self.tournament,
            speech_type=ScoreCriterion.SpeechType.SUBSTANTIVE,
        ).order_by('seq', 'pk')
        return [self._criterion_initial(criterion, order) for order, criterion in enumerate(criteria, start=1)]

    def get_reply_initial(self):
        criteria = ScoreCriterion.objects.filter(
            tournament=self.tournament,
            speech_type=ScoreCriterion.SpeechType.REPLY,
        ).order_by('seq', 'pk')
        return [self._criterion_initial(criterion, order) for order, criterion in enumerate(criteria, start=1)]

    def get_cross_initial(self):
        crosses = CrossExamination.objects.filter(tournament=self.tournament).order_by('seq', 'pk')
        return [self._criterion_initial(cross, order) for order, cross in enumerate(crosses, start=1)]

    def get_formsets(self):
        if self.request.method == 'POST' and self.request.POST.get('action') == 'save_criteria':
            return {
                'substantive': ScoreCriterionFormSet(self.request.POST, prefix='substantive'),
                'reply': ScoreCriterionFormSet(self.request.POST, prefix='reply'),
                'cross': CrossCriterionFormSet(self.request.POST, prefix='cross'),
            }
        return {
            'substantive': ScoreCriterionFormSet(prefix='substantive', initial=self.get_substantive_initial()),
            'reply': ScoreCriterionFormSet(prefix='reply', initial=self.get_reply_initial()),
            'cross': CrossCriterionFormSet(prefix='cross', initial=self.get_cross_initial()),
        }

    def get_apply_form(self):
        if self.request.method == 'POST' and self.request.POST.get('action') == 'apply_preset':
            return ApplyCriterionPresetForm(self.request.POST)
        return ApplyCriterionPresetForm()

    def get_save_preset_form(self):
        if self.request.method == 'POST' and self.request.POST.get('action') == 'save_preset':
            return SaveCriterionPresetForm(self.request.POST)
        return SaveCriterionPresetForm()

    def get_delete_preset_form(self):
        if self.request.method == 'POST' and self.request.POST.get('action') == 'delete_preset':
            return DeleteCriterionPresetForm(self.request.POST)
        return DeleteCriterionPresetForm()

    def get_context_data(self, **kwargs):
        kwargs.setdefault('formsets', self.get_formsets())
        kwargs.setdefault('apply_form', self.get_apply_form())
        kwargs.setdefault('save_preset_form', self.get_save_preset_form())
        kwargs.setdefault('delete_preset_form', self.get_delete_preset_form())
        kwargs['presets'] = CriterionPreset.objects.prefetch_related('items').order_by('-builtin', 'name')
        kwargs['deletable_presets'] = CriterionPreset.objects.filter(builtin=False).order_by('name')
        kwargs['has_ballots'] = BallotSubmission.objects.filter(debate__round__tournament=self.tournament).exists()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'save_criteria':
            return self.post_save_criteria()
        if action == 'apply_preset':
            return self.post_apply_preset()
        if action == 'save_preset':
            return self.post_save_preset()
        if action == 'delete_preset':
            return self.post_delete_preset()

        raise Http404

    def post_save_criteria(self):
        formsets = self.get_formsets()
        apply_form = self.get_apply_form()
        save_preset_form = self.get_save_preset_form()
        delete_preset_form = self.get_delete_preset_form()

        if all(formset.is_valid() for formset in formsets.values()):
            save_tournament_criteria(
                self.tournament,
                self._entries_from_formset(formsets['substantive']),
                self._entries_from_formset(formsets['reply']),
                self._entries_from_formset(formsets['cross']),
            )
            messages.success(self.request, _("Criterion configuration saved."))
            return redirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(
            formsets=formsets,
            apply_form=apply_form,
            save_preset_form=save_preset_form,
            delete_preset_form=delete_preset_form,
        ))

    def post_apply_preset(self):
        apply_form = self.get_apply_form()
        if apply_form.is_valid():
            preset = apply_form.cleaned_data['preset']
            apply_preset_to_tournament(preset, self.tournament)
            messages.success(self.request, _("Applied criterion preset '%(preset)s'.") % {'preset': preset.name})
            return redirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(apply_form=apply_form))

    def post_save_preset(self):
        save_preset_form = self.get_save_preset_form()
        if save_preset_form.is_valid():
            preset = create_preset_from_tournament(
                save_preset_form.cleaned_data['name'],
                save_preset_form.cleaned_data['description'],
                self.tournament,
            )
            messages.success(self.request, _("Saved global criterion preset '%(preset)s'.") % {'preset': preset.name})
            return redirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(save_preset_form=save_preset_form))

    def post_delete_preset(self):
        delete_preset_form = self.get_delete_preset_form()
        if delete_preset_form.is_valid():
            preset = delete_preset_form.cleaned_data['preset_id']
            name = preset.name
            preset.delete()
            messages.success(self.request, _("Deleted criterion preset '%(preset)s'.") % {'preset': name})
            return redirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(delete_preset_form=delete_preset_form))

    @staticmethod
    def _criterion_initial(criterion, order):
        return {
            'item_id': criterion.pk,
            'order': order,
            'name': criterion.name,
            'weight': criterion.weight,
            'min_score': criterion.min_score,
            'max_score': criterion.max_score,
            'step': criterion.step,
            'required': criterion.required,
        }

    @staticmethod
    def _entries_from_formset(formset):
        return [entry for entry in (form.entry() for form in formset) if entry is not None]
