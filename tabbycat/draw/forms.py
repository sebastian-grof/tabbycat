from django import forms
from django.core.exceptions import ObjectDoesNotExist
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
    MODE_CLEAR = "clear"

    mode = forms.ChoiceField(
        label=_("Generation mode"),
        choices=(
            (MODE_RANDOM, _("Random")),
            (MODE_OPPOSITE, _("Opposite of round")),
            (MODE_CLEAR, _("Clear selection")),
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


class SideAllocationByeOverrideForm(forms.Form):

    def __init__(self, tournament, selected_round, active_teams=None, *args, **kwargs):
        self.tournament = tournament
        self.selected_round = selected_round
        self.active_teams = list(active_teams if active_teams is not None else selected_round.active_teams.order_by("short_name", "id"))
        super().__init__(*args, **kwargs)

        self.fields["selected_round"] = forms.ModelChoiceField(
            queryset=tournament.prelim_rounds(),
            initial=selected_round,
            widget=forms.HiddenInput,
        )

        active_team_ids = [team.id for team in self.active_teams]
        team_queryset = tournament.team_set.filter(id__in=active_team_ids).order_by("short_name", "id")
        self.fields["team"] = forms.ModelChoiceField(
            label=_("Bye team override"),
            queryset=team_queryset,
            required=False,
            empty_label=_("Automatic (use tournament setting)"),
            widget=forms.Select(attrs={"class": "custom-select form-control"}),
        )

        try:
            current_override = selected_round.bye_team_override
        except ObjectDoesNotExist:
            current_override = None

        if current_override is not None and current_override.team_id in active_team_ids:
            self.initial["team"] = current_override.team

    def clean(self):
        cleaned_data = super().clean()
        team = cleaned_data.get("team")
        if team is None:
            return cleaned_data

        sides_count = len(self.tournament.sides)
        if self.tournament.pref("bye_team_selection") == "off" or sides_count == 0:
            required_byes = 0
        else:
            required_byes = len(self.active_teams) % sides_count

        if required_byes == 0:
            self.add_error("team", _("This round doesn't currently require a bye."))
        elif required_byes != 1:
            self.add_error("team", _("Manual bye overrides are only supported when exactly one bye is required."))

        return cleaned_data

    def get_team(self):
        return self.cleaned_data.get("team")


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
