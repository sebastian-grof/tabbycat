from typing import Union

from .models import ConverterPermission, GlobalConverterPermission

permission_type = Union[ConverterPermission, str]


def has_converter_permission(user, permission: permission_type = ConverterPermission.USE) -> bool:
    if user.is_anonymous:
        return False
    if user.is_superuser:
        return True
    permission_value = permission.value if isinstance(permission, ConverterPermission) else str(permission)
    return GlobalConverterPermission.objects.filter(user=user, permission=permission_value).exists()


def can_use_converter(user) -> bool:
    return has_converter_permission(user, ConverterPermission.USE)


def can_manage_converter_access(user) -> bool:
    return has_converter_permission(user, ConverterPermission.MANAGE_ACCESS)
