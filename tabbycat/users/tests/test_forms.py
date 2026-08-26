from django.test import SimpleTestCase

from users.forms import PERMISSION_GROUPS
from users.permissions import Permission


class PermissionGroupsTests(SimpleTestCase):
    """PERMISSION_GROUPS drives the checkboxes in RoleManagementView, so a
    permission missing from it can never be granted through the interface.
    Upstream syncs regularly add permissions, hence this guard."""

    def test_every_permission_is_offered_in_the_role_editor(self):
        listed = [p for _, permissions in PERMISSION_GROUPS for p in permissions]
        self.assertEqual(set(listed), set(Permission))

    def test_no_permission_is_listed_twice(self):
        listed = [p for _, permissions in PERMISSION_GROUPS for p in permissions]
        self.assertEqual(len(listed), len(set(listed)))
