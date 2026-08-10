from django.contrib.auth import get_user_model
from django.test import override_settings, TestCase
from django.urls import reverse

from tournaments.models import Round, Tournament, TournamentCategory
from users.groups import TabAssistant
from users.models import Group, Membership, UserPermission
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

    def make_user_with_direct_permissions(self, username, permissions):
        user = get_user_model().objects.create_user(username=username, password="password")
        for permission in permissions:
            UserPermission.objects.create(user=user, permission=permission, tournament=self.tournament)
        return user

    def test_direct_assistant_permissions_do_not_grant_admin_access(self):
        # Regression: assistant-interface permissions granted *directly* (not via
        # a group) must stay assistant-only and not confer full admin access.
        user = self.make_user_with_direct_permissions(
            "direct-assistant", [Permission.ACCESS_ASSISTANT, Permission.VIEW_PARTICIPANTS])
        self.client.force_login(user)

        self.assertEqual(
            self.client.get(reverse_tournament("tournament-admin-home", self.tournament)).status_code, 403)
        self.assertEqual(
            self.client.get(reverse_tournament("tournament-assistant-home", self.tournament)).status_code, 200)

    def test_direct_admin_permission_grants_admin_access(self):
        user = self.make_user_with_direct_permissions("direct-admin", [Permission.VIEW_SETTINGS])
        self.client.force_login(user)

        self.assertEqual(
            self.client.get(reverse_tournament("tournament-admin-home", self.tournament)).status_code, 200)

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

    def test_user_without_role_cannot_access_assistant_home(self):
        user = get_user_model().objects.create_user(username="norole", password="password")
        self.client.force_login(user)

        response = self.client.get(reverse_tournament("tournament-assistant-home", self.tournament))

        self.assertEqual(response.status_code, 403)

    def test_assistant_role_does_not_grant_access_to_other_tournaments(self):
        user = self.make_user("scoped-assistant", TabAssistant.permissions)
        self.client.force_login(user)

        other = Tournament.objects.create(slug="other-access", name="Other Access")
        Round.objects.create(
            tournament=other,
            seq=1,
            name="Round 1",
            abbreviation="R1",
            draw_type=Round.DrawType.RANDOM,
        )
        other.current_round = other.round_set.first()
        other.save()

        response = self.client.get(reverse_tournament("tournament-assistant-home", other))

        self.assertEqual(response.status_code, 403)

    # The site default language is Slovak, so the nav labels these tests look
    # for are only in English when the language is pinned.
    @override_settings(LANGUAGE_CODE='en')
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

    @override_settings(LANGUAGE_CODE='en')
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


class TournamentCategoryVisibilityTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.public_category = TournamentCategory.objects.create(
            name="Public Folder",
            slug="public-folder",
            public=True,
        )
        cls.private_category = TournamentCategory.objects.create(
            name="Private Folder",
            slug="private-folder",
            public=False,
        )
        cls.public_tournament = Tournament.objects.create(
            slug="public-tournament",
            name="Public Tournament",
            homepage_category=cls.public_category,
        )
        cls.private_tournament = Tournament.objects.create(
            slug="private-tournament",
            name="Private Tournament",
            homepage_category=cls.private_category,
        )
        cls.other_private_tournament = Tournament.objects.create(
            slug="other-private-tournament",
            name="Other Private Tournament",
            homepage_category=cls.private_category,
        )

    def make_user(self, username, tournament=None, permissions=None):
        user = get_user_model().objects.create_user(username=username, password="password")
        if tournament is not None:
            group = Group.objects.create(
                name=f"{username} group",
                tournament=tournament,
                permissions=list(permissions or [Permission.VIEW_SETTINGS]),
            )
            Membership.objects.create(user=user, group=group)
        return user

    def test_public_category_visible_to_anonymous_user(self):
        response = self.client.get("/")

        self.assertContains(response, "Public Folder")
        self.assertNotContains(response, "Private Folder")

    def test_private_category_url_hidden_from_anonymous_user(self):
        response = self.client.get(reverse("tournament-category", kwargs={"category_slug": self.private_category.slug}))

        self.assertEqual(response.status_code, 404)

    def test_private_category_visible_to_tournament_admin(self):
        user = self.make_user("private-admin", self.private_tournament)
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertContains(response, "Private Folder")

    def test_private_category_page_only_lists_accessible_tournaments(self):
        user = self.make_user("private-admin-page", self.private_tournament)
        self.client.force_login(user)

        response = self.client.get(reverse("tournament-category", kwargs={"category_slug": self.private_category.slug}))

        self.assertContains(response, "Private Tournament")
        self.assertNotContains(response, "Other Private Tournament")

    @override_settings(LANGUAGE_CODE='en')
    def test_navbar_does_not_offer_areas_for_tournaments_without_a_role(self):
        # The tournament switcher is rendered on every page, so it must apply
        # the same visibility rules as the category listings: a user with no
        # role in a private-category tournament should not be offered its
        # assistant or public area.
        user = self.make_user("private-admin-nav", self.private_tournament)
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertContains(response, reverse_tournament("tournament-admin-home", self.private_tournament))
        self.assertNotContains(
            response, reverse_tournament("tournament-assistant-home", self.other_private_tournament))
        self.assertNotContains(
            response, reverse_tournament("tournament-public-index", self.other_private_tournament))

    @override_settings(LANGUAGE_CODE='en')
    def test_navbar_does_not_offer_assistant_area_without_assistant_access(self):
        # Any authenticated user used to be offered every tournament's
        # assistant area, which then 403s for users holding no role there.
        user = self.make_user("roleless")
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertContains(response, reverse_tournament("tournament-public-index", self.public_tournament))
        self.assertNotContains(
            response, reverse_tournament("tournament-assistant-home", self.public_tournament))

    def test_assistant_only_access_does_not_show_private_category(self):
        user = self.make_user("assistant", self.private_tournament, TabAssistant.permissions)
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertNotContains(response, "Private Folder")
