from typing import Union

from .models import ConverterPermission, GlobalConverterPermission

permission_type = Union[ConverterPermission, str]


def has_converter_permission(user, permission: permission_type = ConverterPermission.USE) -> bool:
    if user.is_anonymous:
        return False
    if user.is_superuser:
        return True
    return GlobalConverterPermission.objects.filter(user=user, permission=str(permission)).exists()
