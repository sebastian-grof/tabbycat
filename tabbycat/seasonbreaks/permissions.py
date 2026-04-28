from typing import Union

from .models import BreaksPermission, GlobalBreaksPermission

permission_type = Union[BreaksPermission, str]


def has_breaks_permission(user, permission: permission_type) -> bool:
    if user.is_anonymous:
        return False
    if user.is_superuser:
        return True
    return GlobalBreaksPermission.objects.filter(user=user, permission=str(permission)).exists()


def can_view_breaks(user) -> bool:
    return has_breaks_permission(user, BreaksPermission.VIEW)


def can_edit_breaks(user) -> bool:
    return has_breaks_permission(user, BreaksPermission.EDIT)


def can_manage_breaks_access(user) -> bool:
    return has_breaks_permission(user, BreaksPermission.MANAGE_ACCESS)
