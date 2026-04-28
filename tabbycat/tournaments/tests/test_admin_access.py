from django.contrib.auth import get_user_model
from django.test import TestCase

from tournaments.models import Round, Tournament
from users.groups import TabAssistant
from users.models import Group, Membership
from users.permissions import Permission
from utils.misc import reverse_tournament


class AdminAccessTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.tournament = Tournament.objects.create(slug="admin-access", name="Admin Access")
        cls.round = Round.objects.create(
            tournament=cls.tournament,
            seq=1,
            name="Round 1",
            abbreviation="R1",
            draw_type=Round.DrawType.RANDOM,
        )
        cls.tournament.current_round = cls.round
        cls.tournament.save()

    def make_user(self, username, permissions):
        user = get_user_model().objects.create_user(username=username, password="password")
        group = Group.objects.create(
            name=f"{username} group",
            tournament=self.tournament,
            permissions=list(permissions),
        )
        Membership.objects.create(user=user, group=group)
        return user

    def test_assistant_only_user_cannot_access_admin_home(self):
        user = self.make_user("assistant", TabAssistant.permissions)
        self.client.force_login(user)

        response = self.client.get(reverse_tournament("tournament-admin-home", self.tournament))

        self.assertEqual(response.status_code, 403)

    def test_assistant_only_user_cannot_access_admin_view_with_assistant_permission(self):
        user = self.make_user("assistant", TabAssistant.permissions)
        self.client.force_login(user)

        response = self.client.get(reverse_tournament("admin-checkin-prescan", self.tournament))

        self.assertEqual(response.status_code, 403)

    def test_assistant_only_user_can_access_assistant_home(self):
        user = self.make_user("assistant", TabAssistant.permissions)
        self.client.force_login(user)

        response = self.client.get(reverse_tournament("tournament-assistant-home", self.tournament))

        self.assertEqual(response.status_code, 200)

    def test_assistant_only_user_does_not_see_admin_area_link(self):
        user = self.make_user("assistant", TabAssistant.permissions)
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertNotContains(response, reverse_tournament("tournament-admin-home", self.tournament))
        self.assertNotContains(response, "Administrator area")

    def test_user_with_admin_permission_can_access_admin_home(self):
        user = self.make_user("settings", [Permission.VIEW_SETTINGS])
        self.client.force_login(user)

        response = self.client.get(reverse_tournament("tournament-admin-home", self.tournament))

        self.assertEqual(response.status_code, 200)

    def test_user_with_admin_permission_sees_admin_area_link(self):
        user = self.make_user("settings", [Permission.VIEW_SETTINGS])
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertContains(response, reverse_tournament("tournament-admin-home", self.tournament))
        self.assertContains(response, "Administrator area")

    def test_superuser_can_access_admin_home(self):
        user = get_user_model().objects.create_superuser("superuser", password="password")
        self.client.force_login(user)

        response = self.client.get(reverse_tournament("tournament-admin-home", self.tournament))

        self.assertEqual(response.status_code, 200)

    def test_non_superuser_cannot_manage_roles(self):
        user = self.make_user("role-manager", [Permission.VIEW_SETTINGS, Permission.EDIT_SETTINGS])
        self.client.force_login(user)

        response = self.client.get(reverse_tournament("user-role-management", self.tournament))

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_manage_roles(self):
        user = get_user_model().objects.create_superuser("role-superuser", password="password")
        self.client.force_login(user)

        response = self.client.get(reverse_tournament("user-role-management", self.tournament))

        self.assertEqual(response.status_code, 200)
