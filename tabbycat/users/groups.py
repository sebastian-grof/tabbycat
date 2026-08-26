from typing import List, Optional

from django.utils.translation import gettext_lazy as _

from options.presets import _all_subclasses

from .permissions import ASSISTANT_INTERFACE_PERMISSIONS, Permission


def all_groups():
    yield from _all_subclasses(BaseGroup)


ADJUDICATION_CORE_FEEDBACK_VIEW_PERMISSIONS = frozenset({
    Permission.VIEW_FEEDBACK_OVERVIEW,
    Permission.EDIT_BASEJUDGESCORES_IND,
    Permission.VIEW_FEEDBACK,
    Permission.EDIT_FEEDBACK_IGNORE,
    Permission.EDIT_FEEDBACK_CONFIRM,
    Permission.VIEW_FEEDBACK_UNSUBMITTED,
    Permission.EDIT_FEEDBACKQUESTION,
})


class BaseGroup:
    name: Optional[str] = None
    permissions: List[Permission] = []


class Equity(BaseGroup):
    name = _("Equity")
    permissions = [
        # View and edit all conflicts
        Permission.VIEW_ADJ_TEAM_CONFLICTS,
        Permission.EDIT_ADJ_TEAM_CONFLICTS,
        Permission.VIEW_ADJ_ADJ_CONFLICTS,
        Permission.EDIT_ADJ_ADJ_CONFLICTS,
        Permission.VIEW_ADJ_INST_CONFLICTS,
        Permission.EDIT_ADJ_INST_CONFLICTS,
        Permission.VIEW_TEAM_INST_CONFLICTS,
        Permission.EDIT_TEAM_INST_CONFLICTS,

        # Room constraints
        Permission.VIEW_ROOMCONSTRAINTS,
        Permission.EDIT_ROOMCONSTRAINTS,
        Permission.VIEW_ROOMCATEGORIES,
        Permission.EDIT_ROOMCATEGORIES,

        # Participant identity info
        Permission.VIEW_PARTICIPANTS,
        Permission.VIEW_PARTICIPANT_GENDER,
        Permission.VIEW_PARTICIPANT_CONTACT,
        Permission.VIEW_PARTICIPANT_DECODED,
        Permission.VIEW_PARTICIPANT_INST,
        Permission.VIEW_DECODED_TEAMS,
        Permission.VIEW_ANONYMOUS,

        # Supporting context
        Permission.VIEW_TEAMS,
        Permission.VIEW_ADJUDICATORS,
        Permission.VIEW_ROOMS,
        Permission.VIEW_INSTITUTIONS,
    ]


class AdjudicationCore(BaseGroup):
    # All tournament permissions except feedback viewing/admin feedback controls.
    # Adjudication core may enter feedback, matching the assistant interface.
    name = _("Adjudication Core")
    permissions = [
        permission for permission in Permission
        if permission not in ADJUDICATION_CORE_FEEDBACK_VIEW_PERMISSIONS
    ]


class TabDirector(BaseGroup):
    # All permissions
    name = _("Tabulation Director")
    permissions = [p for p in Permission]


class TabAssistant(BaseGroup):
    # Permissions to match the Assistant interface
    name = _("Tabulation Assistant")
    permissions = list(ASSISTANT_INTERFACE_PERMISSIONS)


class Registration(BaseGroup):
    name = _("Registration")
    permissions = [
        Permission.ADD_TEAMS,
        Permission.DELETE_SPEAKER,
        Permission.VIEW_DECODED_TEAMS,
        Permission.VIEW_ANONYMOUS,
        Permission.ADD_ADJUDICATORS,
        Permission.ADD_INSTITUTIONS,
        Permission.VIEW_PARTICIPANTS,
        Permission.VIEW_PARTICIPANT_GENDER,
        Permission.VIEW_PARTICIPANT_CONTACT,
        Permission.VIEW_PARTICIPANT_DECODED,
        Permission.VIEW_PARTICIPANT_INST,
        Permission.VIEW_SETTINGS,
        Permission.EDIT_QUESTIONS,
        Permission.DELETE_QUESTIONS,
        Permission.VIEW_CUSTOM_ANSWERS,
        Permission.VIEW_REGISTRATION,
        Permission.EDIT_REGISTRATION_SLOTS,
    ]
