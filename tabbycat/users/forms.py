from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm, UserCreationForm, UsernameField
from django.core.cache import cache
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import Group, Membership
from .permissions import PERM_CACHE_KEY, Permission


PERMISSION_GROUPS = (
    (_("Conflicts"), (
        Permission.VIEW_ADJ_TEAM_CONFLICTS,
        Permission.EDIT_ADJ_TEAM_CONFLICTS,
        Permission.VIEW_ADJ_ADJ_CONFLICTS,
        Permission.EDIT_ADJ_ADJ_CONFLICTS,
        Permission.VIEW_ADJ_INST_CONFLICTS,
        Permission.EDIT_ADJ_INST_CONFLICTS,
        Permission.VIEW_TEAM_INST_CONFLICTS,
        Permission.EDIT_TEAM_INST_CONFLICTS,
    )),
    (_("Participants"), (
        Permission.VIEW_TEAMS,
        Permission.ADD_TEAMS,
        Permission.VIEW_DECODED_TEAMS,
        Permission.VIEW_ANONYMOUS,
        Permission.VIEW_ADJUDICATORS,
        Permission.ADD_ADJUDICATORS,
        Permission.VIEW_ROOMS,
        Permission.ADD_ROOMS,
        Permission.VIEW_INSTITUTIONS,
        Permission.ADD_INSTITUTIONS,
        Permission.VIEW_PARTICIPANTS,
        Permission.VIEW_PARTICIPANT_GENDER,
        Permission.VIEW_PARTICIPANT_CONTACT,
        Permission.VIEW_PARTICIPANT_DECODED,
        Permission.VIEW_PARTICIPANT_INST,
    )),
    (_("Availability"), (
        Permission.VIEW_ROUNDAVAILABILITIES_TEAM,
        Permission.VIEW_ROUNDAVAILABILITIES_ADJ,
        Permission.VIEW_ROUNDAVAILABILITIES_VENUE,
        Permission.EDIT_ROUNDAVAILABILITIES_TEAM,
        Permission.EDIT_ROUNDAVAILABILITIES_ADJ,
        Permission.EDIT_ROUNDAVAILABILITIES_VENUE,
        Permission.VIEW_ROUNDAVAILABILITIES,
        Permission.EDIT_ROUNDAVAILABILITIES,
    )),
    (_("Rooms"), (
        Permission.VIEW_ROOMCONSTRAINTS,
        Permission.VIEW_ROOMCATEGORIES,
        Permission.EDIT_ROOMCONSTRAINTS,
        Permission.EDIT_ROOMCATEGORIES,
    )),
    (_("Pairing"), (
        Permission.VIEW_DEBATE,
        Permission.VIEW_ADMIN_DRAW,
        Permission.GENERATE_DEBATE,
        Permission.DELETE_DEBATE,
        Permission.EDIT_DEBATETEAMS,
        Permission.VIEW_DEBATEADJUDICATORS,
        Permission.EDIT_DEBATEADJUDICATORS,
        Permission.VIEW_ROOMALLOCATIONS,
        Permission.EDIT_ROOMALLOCATIONS,
        Permission.EDIT_ALLOCATESIDES,
        Permission.VIEW_BRIEFING_DRAW,
        Permission.DISPLAY_MOTION,
        Permission.VIEW_PREFORMEDPANELS,
        Permission.EDIT_PREFORMEDPANELS,
    )),
    (_("Ballots and Results"), (
        Permission.VIEW_NEW_BALLOTSUBMISSIONS,
        Permission.EDIT_OLD_BALLOTSUBMISSIONS,
        Permission.VIEW_BALLOTSUBMISSIONS,
        Permission.EDIT_BALLOTSUBMISSIONS,
        Permission.ADD_BALLOTSUBMISSIONS,
        Permission.MARK_BALLOTSUBMISSIONS,
        Permission.MARK_OTHERS_BALLOTSUBMISSIONS,
        Permission.VIEW_BALLOTSUBMISSION_GRAPH,
        Permission.VIEW_RESULTS,
    )),
    (_("Motions and Release"), (
        Permission.VIEW_MOTION,
        Permission.EDIT_MOTION,
        Permission.RELEASE_DRAW,
        Permission.RELEASE_MOTION,
        Permission.UNRELEASE_DRAW,
        Permission.UNRELEASE_MOTION,
        Permission.EDIT_STARTTIME,
    )),
    (_("Standings"), (
        Permission.VIEW_STANDINGS_OVERVIEW,
        Permission.VIEW_TEAMSTANDINGS,
        Permission.VIEW_SPEAKERSSTANDINGS,
        Permission.VIEW_REPLIESSTANDINGS,
        Permission.VIEW_MOTIONSTAB,
        Permission.VIEW_DIVERSITYTAB,
    )),
    (_("Feedback"), (
        Permission.VIEW_FEEDBACK_OVERVIEW,
        Permission.EDIT_BASEJUDGESCORES_IND,
        Permission.VIEW_FEEDBACK,
        Permission.EDIT_FEEDBACK_IGNORE,
        Permission.EDIT_FEEDBACK_CONFIRM,
        Permission.VIEW_FEEDBACK_UNSUBMITTED,
        Permission.ADD_FEEDBACK,
        Permission.EDIT_FEEDBACKQUESTION,
    )),
    (_("Breaks"), (
        Permission.VIEW_ADJ_BREAK,
        Permission.EDIT_ADJ_BREAK,
        Permission.EDIT_BREAK_ELIGIBILITY,
        Permission.VIEW_BREAK_ELIGIBILITY,
        Permission.EDIT_BREAK_CATEGORIES,
        Permission.VIEW_BREAK_CATEGORIES,
        Permission.VIEW_SPEAKER_CATEGORIES,
        Permission.EDIT_SPEAKER_CATEGORIES,
        Permission.VIEW_SPEAKER_ELIGIBILITY,
        Permission.EDIT_SPEAKER_ELIGIBILITY,
        Permission.VIEW_BREAK_OVERVIEW,
        Permission.VIEW_BREAK,
        Permission.GENERATE_BREAK,
    )),
    (_("Check-Ins and Private URLs"), (
        Permission.VIEW_PRIVATE_URLS,
        Permission.GENERATE_PRIVATE_URLS,
        Permission.VIEW_CHECKIN,
        Permission.EDIT_PARTICIPANT_CHECKIN,
        Permission.EDIT_ROOM_CHECKIN,
        Permission.EDIT_DEBATE_CHECKIN,
    )),
    (_("Rounds and Schedule"), (
        Permission.EDIT_ROUND,
        Permission.DELETE_ROUND,
        Permission.CREATE_ROUND,
        Permission.CONFIRM_ROUND,
        Permission.SILENCE_ROUND,
        Permission.EDIT_EVENTS,
        Permission.VIEW_EVENTS,
    )),
    (_("Settings, Data and Registration"), (
        Permission.VIEW_ACTIONLOGENTRIES,
        Permission.VIEW_EMAIL_STATUSES,
        Permission.SEND_EMAILS,
        Permission.EXPORT_XML,
        Permission.VIEW_SETTINGS,
        Permission.EDIT_SETTINGS,
        Permission.EDIT_QUESTIONS,
        Permission.DELETE_QUESTIONS,
        Permission.VIEW_CUSTOM_ANSWERS,
        Permission.VIEW_REGISTRATION,
        Permission.EDIT_REGISTRATION,
        Permission.CONFIRM_REGISTRATION,
    )),
)


class SuperuserCreationForm(UserCreationForm):
    """A form that creates a superuser from the given username and password."""

    class Meta(UserCreationForm.Meta):
        fields = ("username", "email")
        labels = {"email": _("Email address")}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        user.is_superuser = True
        if commit:
            user.save()
        return user


class InviteUserForm(PasswordResetForm):
    def __init__(self, tournament, *args, **kwargs):
        self.tournament = tournament
        super().__init__(*args, **kwargs)

        self.fields['role'] = forms.ModelChoiceField(queryset=tournament.group_set.all())

    def get_users(self, email):
        user, created = get_user_model().objects.get_or_create(
            email=email,
            defaults={
                'username': email.split("@")[0],
            },
        )
        Membership.objects.get_or_create(
            user=user,
            group=self.cleaned_data['role'],
        )

        return [user]

    def save(self, *args, **kwargs):
        kwargs['extra_email_context'] = {**(kwargs['extra_email_context'] or {}), 'tournament': self.tournament}
        return super().save(*args, **kwargs)


class AcceptInvitationForm(SetPasswordForm):
    username = UsernameField(label=_("Username"), help_text=get_user_model()._meta.get_field('username').help_text)

    field_order = ('username', 'new_password1', 'new_password2')

    def save(self, commit=True):
        self.user.username = self.cleaned_data['username']
        return super().save(commit=commit)


class RoleForm(forms.Form):
    role_id = forms.ModelChoiceField(queryset=Group.objects.none(), widget=forms.HiddenInput, required=False)
    name = forms.CharField(max_length=100, label=_("Role name"))
    permissions = forms.MultipleChoiceField(
        choices=Permission.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Permissions"),
    )

    def __init__(self, tournament, *args, instance=None, **kwargs):
        self.tournament = tournament
        self.instance = instance
        initial = kwargs.pop('initial', {})
        if instance is not None:
            initial = {
                **initial,
                'role_id': instance.pk,
                'name': instance.name,
                'permissions': instance.permissions,
            }
        super().__init__(*args, initial=initial, **kwargs)
        self.fields['role_id'].queryset = tournament.group_set.all()

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        qs = self.tournament.group_set.filter(name__iexact=name)
        role = self.cleaned_data.get('role_id') or self.instance
        if role is not None:
            qs = qs.exclude(pk=role.pk)
        if qs.exists():
            raise forms.ValidationError(_("A role with this name already exists in this tournament."))
        return name

    def save(self):
        role = self.cleaned_data.get('role_id') or self.instance
        permissions = self.cleaned_data['permissions']
        old_permissions = set(role.permissions) if role is not None else set()

        if role is None:
            role = Group(tournament=self.tournament)

        role.name = self.cleaned_data['name']
        role.permissions = permissions
        role.save()

        self._clear_membership_permission_cache(role, old_permissions | set(permissions))
        self.instance = role
        return role

    def _clear_membership_permission_cache(self, role, permissions):
        if not permissions:
            return
        cache.delete_many([
            PERM_CACHE_KEY % (user_id, self.tournament.slug, permission)
            for user_id in role.users.values_list('id', flat=True)
            for permission in permissions
        ])


class AssignUserRolesForm(forms.Form):
    user = forms.ModelChoiceField(queryset=get_user_model().objects.none(), label=_("User"))
    roles = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Roles"),
    )

    def __init__(self, tournament, *args, user_instance=None, **kwargs):
        self.tournament = tournament
        self.user_instance = user_instance
        initial = kwargs.pop('initial', {})
        if user_instance is not None:
            initial = {
                **initial,
                'user': user_instance.pk,
                'roles': user_instance.group_set.filter(tournament=tournament).values_list('pk', flat=True),
            }
        super().__init__(*args, initial=initial, **kwargs)
        self.fields['user'].queryset = get_user_model().objects.order_by('username', 'email')
        self.fields['roles'].queryset = tournament.group_set.order_by('name')

    @transaction.atomic
    def save(self):
        user = self.cleaned_data['user']
        selected_roles = list(self.cleaned_data['roles'])
        current_memberships = Membership.objects.filter(user=user, group__tournament=self.tournament)

        selected_role_ids = {role.pk for role in selected_roles}
        current_memberships.exclude(group_id__in=selected_role_ids).delete()

        existing_role_ids = set(current_memberships.values_list('group_id', flat=True))
        for role in selected_roles:
            if role.pk not in existing_role_ids:
                Membership.objects.create(user=user, group=role)

        return user
