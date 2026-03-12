from django import forms
from django.utils.translation import gettext as _

from tournaments.utils import get_side_name


class ConfirmDrawDeletionForm(forms.Form):
    round_name = forms.CharField(label=_("Full round name"), required=True)
    overwrite_preformed_panels = forms.BooleanField(
        label=_("Overwrite preformed panels with current panels"),
        required=False,
    )

    def __init__(self, round, **kwargs):
        self.round = round
        super().__init__(**kwargs)

    def clean_round_name(self):
        if self.cleaned_data['round_name'] != self.round.name:
            raise forms.ValidationError(_("You must type '%s' to confirm draw and results deletion.") % self.round.name)


class SideAllocationGenerateForm(forms.Form):
    MODE_RANDOM = "random"
    MODE_OPPOSITE = "opposite"

    mode = forms.ChoiceField(
        label=_("Generation mode"),
        choices=(
            (MODE_RANDOM, _("Random")),
            (MODE_OPPOSITE, _("Opposite of round")),
        ),
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )

    def __init__(self, tournament, selected_round=None, *args, **kwargs):
        self.tournament = tournament
        super().__init__(*args, **kwargs)

        prelim_rounds = tournament.prelim_rounds()

        self.fields["target_round"] = forms.ModelChoiceField(
            label=_("Target round"),
            queryset=prelim_rounds,
            initial=selected_round,
            widget=forms.Select(attrs={"class": "custom-select form-control"}),
        )
        self.fields["source_round"] = forms.ModelChoiceField(
            label=_("Source round"),
            queryset=prelim_rounds,
            required=False,
            widget=forms.Select(attrs={"class": "custom-select form-control"}),
        )

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get("mode")
        target_round = cleaned_data.get("target_round")
        source_round = cleaned_data.get("source_round")

        if mode == self.MODE_OPPOSITE and source_round is None:
            self.add_error("source_round", _("Choose a source round when using opposite-side generation."))

        if target_round is not None and source_round is not None and target_round == source_round:
            self.add_error("source_round", _("The source round must be different from the target round."))

        return cleaned_data


class SideAllocationManualForm(forms.Form):

    def __init__(self, tournament, selected_round, teams=None, *args, **kwargs):
        self.tournament = tournament
        self.selected_round = selected_round
        self.teams = list(teams if teams is not None else tournament.team_set.order_by("short_name", "id"))
        super().__init__(*args, **kwargs)

        self.fields["selected_round"] = forms.ModelChoiceField(
            queryset=tournament.prelim_rounds(),
            initial=selected_round,
            widget=forms.HiddenInput,
        )

        current_allocations = {
            tsa.team_id: str(tsa.side) for tsa in selected_round.teamsideallocation_set.all()
        }
        side_choices = [("", _("Unassigned"))] + [
            (str(side), get_side_name(tournament, side, "full").capitalize())
            for side in tournament.sides
        ]

        for team in self.teams:
            self.fields[self._field_name(team.id)] = forms.ChoiceField(
                label=team.short_name,
                choices=side_choices,
                required=False,
                initial=current_allocations.get(team.id, ""),
                widget=forms.Select(attrs={"class": "custom-select form-control"}),
            )

    @staticmethod
    def _field_name(team_id):
        return f"team_{team_id}"

    def get_allocations(self):
        return {
            team.id: (int(self.cleaned_data[self._field_name(team.id)]) if self.cleaned_data[self._field_name(team.id)] != "" else None)
            for team in self.teams
        }
