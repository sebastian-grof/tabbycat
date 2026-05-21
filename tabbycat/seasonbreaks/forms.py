from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from tournaments.models import Tournament

from .models import (
    BreakAdjudicator,
    BreakLeague,
    BreakRegion,
    BreakSeason,
    BreakSpeaker,
    BreakTeam,
    BreaksPermission,
    BreakTournament,
    GlobalBreaksPermission,
)


class BreakLeagueForm(forms.ModelForm):
    slug = forms.SlugField(required=False)

    class Meta:
        model = BreakLeague
        fields = ('name', 'slug')

    def clean_slug(self):
        slug = self.cleaned_data.get('slug') or slugify(self.cleaned_data.get('name', ''))
        slug = slug[:80]
        if not slug:
            raise ValidationError(_("Enter a valid slug."))
        return slug


class BreakSeasonForm(forms.ModelForm):
    class Meta:
        model = BreakSeason
        fields = ('name', 'slug', 'league', 'regional_slots', 'invited_teams', 'active', 'public')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['league'].queryset = BreakLeague.objects.order_by('name')


class BreakRegionForm(forms.ModelForm):
    class Meta:
        model = BreakRegion
        fields = ('name', 'source_region', 'seq')


class BreakTournamentForm(forms.ModelForm):
    tournament = forms.ModelChoiceField(queryset=Tournament.objects.order_by('seq', 'name'))

    class Meta:
        model = BreakTournament
        fields = ('tournament', 'region', 'seq', 'counts_for_break')

    def __init__(self, *args, season=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season
        self.fields['region'].queryset = season.regions.all() if season else BreakRegion.objects.none()
        if season:
            self.fields['tournament'].queryset = Tournament.objects.exclude(
                break_tournaments__season=season,
            ).order_by('seq', 'name')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.season = self.season
        if commit:
            instance.save()
        return instance


class BreakTeamForm(forms.ModelForm):
    class Meta:
        model = BreakTeam
        fields = ('name', 'institution', 'region')

    def __init__(self, *args, season=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season
        self.fields['region'].queryset = season.regions.all() if season else BreakRegion.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.season = self.season
        if commit:
            instance.save()
        return instance


class BreakSpeakerForm(forms.ModelForm):
    class Meta:
        model = BreakSpeaker
        fields = ('name', 'email')

    def __init__(self, *args, season=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.season = self.season
        if commit:
            instance.save()
        return instance


class BreakAdjudicatorForm(forms.ModelForm):
    class Meta:
        model = BreakAdjudicator
        fields = ('name', 'email', 'institution')

    def __init__(self, *args, season=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.season = self.season
        if commit:
            instance.save()
        return instance


class BreaksAccessForm(forms.Form):
    user = forms.ModelChoiceField(queryset=get_user_model().objects.order_by('username'), label=_("User"))
    permissions = forms.MultipleChoiceField(
        choices=BreaksPermission.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Permissions"),
    )

    def save(self):
        user = self.cleaned_data['user']
        permissions = set(self.cleaned_data['permissions'])
        if BreaksPermission.EDIT in permissions or BreaksPermission.MANAGE_ACCESS in permissions:
            permissions.add(BreaksPermission.VIEW)
        GlobalBreaksPermission.objects.filter(user=user).delete()
        GlobalBreaksPermission.objects.bulk_create([
            GlobalBreaksPermission(user=user, permission=permission)
            for permission in sorted(permissions)
        ])
        return user
