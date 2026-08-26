import logging
from threading import Lock

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import PasswordResetConfirmView
from django.db.models import Q
from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.generic import FormView, TemplateView

from actionlog.mixins import LogActionMixin
from actionlog.models import ActionLogEntry
from tournaments.mixins import TournamentMixin
from utils.misc import reverse_tournament
from utils.mixins import AdministratorMixin

from .forms import (
    AcceptInvitationForm, AssignUserRolesForm, InviteUserForm, PERMISSION_GROUPS, RoleForm,
    SuperuserCreationForm,
)
from .models import Group
from .permissions import Permission

User = get_user_model()
logger = logging.getLogger(__name__)


class BlankSiteStartView(FormView):
    """This view is presented to the user when there are no tournaments and no
    user accounts. It prompts the user to create a first superuser. It rejects
    all requests, GET or POST, if there exists any user account in the
    system."""

    form_class = SuperuserCreationForm
    template_name = "blank_site_start.html"
    lock = Lock()
    success_url = reverse_lazy('tabbycat-index')

    def get(self, request):
        if User.objects.exists():
            logger.warning("Tried to get the blank-site-start view when a user account already exists.")
            return redirect('tabbycat-index')

        return super().get(request)

    def post(self, request):
        with self.lock:
            if User.objects.exists():
                logger.warning("Tried to post the blank-site-start view when a user account already exists.")
                messages.error(request, _("Whoops! It looks like someone's already created the first user account. Please log in."))
                return redirect('login')

            return super().post(request)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.info(self.request, _("Welcome! You've created an account for %s.") % user.username)

        return super().form_valid(form)


class InviteUserView(LogActionMixin, AdministratorMixin, TournamentMixin, FormView):
    """Invite one or more email addresses to create an account and join a tournament role."""

    form_class = InviteUserForm
    template_name = "invite_user.html"
    action_log_type = ActionLogEntry.ActionType.USER_INVITE
    page_title = _("Invite Users")
    page_emoji = '👤'

    subject_template_name = 'account_invitation_subject.txt'
    email_template_name = 'account_invitation_email.html'
    html_email_template_name = None
    extra_email_context = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tournament'] = self.tournament
        return kwargs

    def get_success_url(self):
        return reverse_tournament('options-tournament-index', self.tournament)

    def form_valid(self, form):
        count = form.save(
            request=self.request,
            subject_template_name=self.subject_template_name,
            email_template_name=self.email_template_name,
            html_email_template_name=self.html_email_template_name,
            extra_email_context=self.extra_email_context,
        )
        self.log_action()
        messages.success(self.request, ngettext(
            "Successfully invited %(count)s user to create an account for the tournament.",
            "Successfully invited %(count)s users to create an account for the tournament.",
            count,
        ) % {'count': count})
        return HttpResponseRedirect(self.get_success_url())


class AcceptInvitationView(TournamentMixin, PasswordResetConfirmView):
    form_class = AcceptInvitationForm
    success_url = reverse_lazy('tabbycat-index')
    template_name = 'signup.html'
    page_title = _('Accept Invitation')

    def get_context_data(self, **kwargs):
        if not self.validlink:
            raise Http404
        return super().get_context_data(**kwargs)


class RoleManagementView(AdministratorMixin, TournamentMixin, TemplateView):
    template_name = "role_management.html"
    page_title = _("User Roles")
    page_emoji = '👥'
    view_permission = Permission.VIEW_SETTINGS
    edit_permission = Permission.EDIT_SETTINGS

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser

    def get_selected_role(self):
        role_id = self.request.GET.get('role') or self.request.POST.get('role_id')
        if not role_id:
            return None
        return get_object_or_404(Group, pk=role_id, tournament=self.tournament)

    def get_selected_user(self):
        user_id = self.request.GET.get('user') or self.request.POST.get('user')
        if not user_id:
            return None
        return get_object_or_404(User, pk=user_id)

    def get_role_form(self):
        if self.request.method == 'POST' and self.request.POST.get('action') == 'save_role':
            return RoleForm(self.tournament, self.request.POST, instance=self.get_selected_role())
        return RoleForm(self.tournament, instance=self.get_selected_role())

    def get_assignment_form(self):
        if self.request.method == 'POST' and self.request.POST.get('action') == 'assign_user_roles':
            return AssignUserRolesForm(self.tournament, self.request.POST)
        return AssignUserRolesForm(self.tournament, user_instance=self.get_selected_user())

    def get_active_panel(self):
        if self.request.method == 'POST' and self.request.POST.get('action') == 'save_role':
            return 'roles'
        if self.request.GET.get('panel') == 'roles' or self.request.GET.get('role'):
            return 'roles'
        return 'users'

    def get_permission_groups(self, form, field_name='permissions', id_prefix='permissions'):
        selected = set(form[field_name].value() or [])
        groups = []
        for title, permissions in PERMISSION_GROUPS:
            groups.append({
                'title': title,
                'options': [{
                    'value': permission.value,
                    'label': permission.label,
                    'checked': permission.value in selected,
                    'id': 'id_%s_%s' % (id_prefix, slugify(permission.value)),
                } for permission in permissions],
            })
        return groups

    def get_user_rows(self):
        users = User.objects.filter(
            Q(group_set__tournament=self.tournament) | Q(userpermission__tournament=self.tournament),
        ).distinct()
        users = users.order_by('username', 'email')
        return [{
            'user': user,
            'roles': user.group_set.filter(tournament=self.tournament).order_by('name'),
            'direct_permissions_count': user.userpermission_set.filter(tournament=self.tournament).count(),
        } for user in users]

    def get_context_data(self, **kwargs):
        role_form = kwargs.pop('role_form', self.get_role_form())
        assignment_form = kwargs.pop('assignment_form', self.get_assignment_form())
        kwargs.update({
            'role_form': role_form,
            'assignment_form': assignment_form,
            'permission_groups': self.get_permission_groups(role_form),
            'direct_permission_groups': self.get_permission_groups(
                assignment_form, field_name='direct_permissions', id_prefix='direct_permissions'),
            'roles': self.tournament.group_set.prefetch_related('users').order_by('name'),
            'user_rows': self.get_user_rows(),
            'users_count': User.objects.filter(
                Q(group_set__tournament=self.tournament) | Q(userpermission__tournament=self.tournament),
            ).distinct().count(),
            'active_panel': self.get_active_panel(),
            'selected_role': self.get_selected_role(),
            'selected_user': self.get_selected_user(),
        })
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'save_role':
            role_form = self.get_role_form()
            assignment_form = self.get_assignment_form()
            if role_form.is_valid():
                role = role_form.save()
                messages.success(request, _("Role '%(role)s' saved.") % {'role': role.name})
                return redirect("%s?panel=roles&role=%s" % (
                    reverse_tournament('user-role-management', self.tournament), role.pk))
            return self.render_to_response(self.get_context_data(
                role_form=role_form, assignment_form=assignment_form))

        if action == 'assign_user_roles':
            role_form = self.get_role_form()
            assignment_form = self.get_assignment_form()
            if assignment_form.is_valid():
                user = assignment_form.save()
                messages.success(request, _("Access for %(user)s saved.") % {'user': user})
                return redirect("%s?user=%s" % (
                    reverse_tournament('user-role-management', self.tournament), user.pk))
            return self.render_to_response(self.get_context_data(
                role_form=role_form, assignment_form=assignment_form))

        raise Http404
