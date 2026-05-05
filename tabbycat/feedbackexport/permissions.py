from typing import Union

from .models import FeedbackExportPermission, GlobalFeedbackExportPermission

permission_type = Union[FeedbackExportPermission, str]


def has_feedback_export_permission(user, permission: permission_type = FeedbackExportPermission.VIEW) -> bool:
    if user.is_anonymous:
        return False
    if user.is_superuser:
        return True
    permission_value = permission.value if isinstance(permission, FeedbackExportPermission) else str(permission)
    return GlobalFeedbackExportPermission.objects.filter(user=user, permission=permission_value).exists()


def can_view_feedback_export(user) -> bool:
    return has_feedback_export_permission(user, FeedbackExportPermission.VIEW)


def can_manage_feedback_export(user) -> bool:
    return has_feedback_export_permission(user, FeedbackExportPermission.MANAGE)
