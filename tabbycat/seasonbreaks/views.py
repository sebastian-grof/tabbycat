from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic import TemplateView

from .forms import BreakRegionForm, BreakSeasonForm, BreakSpeakerForm, BreakTeamForm, BreakTournamentForm, BreaksAccessForm
from .models import (
    BreakAdjudicatorTournamentStats,
    BreaksPermission,
    BreakSeason,
    BreakSpeakerLink,
    BreakTeam,
    BreakTeamLink,
    BreakTournament,
    GlobalBreaksPermission,
)
from .permissions import has_breaks_permission
from .services import calculate_rankings, calculate_region_quotas, freeze_break_tournament, season_summary


class BreaksPermissionMixin(UserPassesTestMixin):
    required_permission = BreaksPermission.VIEW
    page_emoji = '🏆'
    page_title = gettext_lazy("Breaks")
    view_role = ''

    def test_func(self):
        return has_breaks_permission(self.request.user, self.required_permission)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('page_title', self.page_title)
        kwargs.setdefault('page_emoji', self.page_emoji)
        kwargs['can_edit_breaks'] = has_breaks_permission(self.request.user, BreaksPermission.EDIT)
        kwargs['can_manage_breaks_access'] = has_breaks_permission(self.request.user, BreaksPermission.MANAGE_ACCESS)
        kwargs['breaks_nav'] = True
        kwargs['user_role'] = self.view_role
        return super().get_context_data(**kwargs)


class BreaksEditMixin(BreaksPermissionMixin):
    required_permission = BreaksPermission.EDIT


class BreaksAccessMixin(BreaksPermissionMixin):
    required_permission = BreaksPermission.MANAGE_ACCESS


class SeasonMixin(BreaksPermissionMixin):
    def dispatch(self, request, *args, **kwargs):
        self.season = get_object_or_404(BreakSeason, slug=kwargs['season_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['season'] = self.season
        kwargs['season_tabs'] = season_tabs(self.season)
        return super().get_context_data(**kwargs)


def season_tabs(season):
    return [
        (_("Overview"), reverse('seasonbreaks-season-overview', kwargs={'season_slug': season.slug}), 'overview'),
        (_("Tournaments"), reverse('seasonbreaks-tournaments', kwargs={'season_slug': season.slug}), 'tournaments'),
        (_("Teams"), reverse('seasonbreaks-teams', kwargs={'season_slug': season.slug}), 'teams'),
        (_("Speakers"), reverse('seasonbreaks-speakers', kwargs={'season_slug': season.slug}), 'speakers'),
        (_("Quotas"), reverse('seasonbreaks-quotas', kwargs={'season_slug': season.slug}), 'quotas'),
        (_("Rankings"), reverse('seasonbreaks-rankings', kwargs={'season_slug': season.slug}), 'rankings'),
        (_("Adjudicators"), reverse('seasonbreaks-adjudicators', kwargs={'season_slug': season.slug}), 'adjudicators'),
        (_("Access"), reverse('seasonbreaks-access'), 'access'),
    ]


class BreaksIndexView(BreaksPermissionMixin, TemplateView):
    template_name = 'seasonbreaks/index.html'

    def get_context_data(self, **kwargs):
        kwargs['seasons'] = BreakSeason.objects.all()
        kwargs['season_form'] = kwargs.get('season_form') or BreakSeasonForm()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not has_breaks_permission(request.user, BreaksPermission.EDIT):
            return self.handle_no_permission()
        form = BreakSeasonForm(request.POST)
        if form.is_valid():
            season = form.save()
            messages.success(request, _("Break season %(season)s was created.") % {'season': season})
            return redirect('seasonbreaks-season-overview', season_slug=season.slug)
        return self.render_to_response(self.get_context_data(season_form=form))


class SeasonOverviewView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/overview.html'

    def get_context_data(self, **kwargs):
        kwargs['summary'] = season_summary(self.season)
        kwargs['quotas'] = calculate_region_quotas(self.season)
        kwargs['active_tab'] = 'overview'
        return super().get_context_data(**kwargs)


class SeasonTournamentsView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/tournaments.html'

    def get_context_data(self, **kwargs):
        kwargs['tournaments'] = self.season.break_tournaments.select_related('tournament', 'region')
        kwargs['regions'] = self.season.regions.all()
        kwargs['region_form'] = kwargs.get('region_form') or BreakRegionForm()
        kwargs['tournament_form'] = kwargs.get('tournament_form') or BreakTournamentForm(season=self.season)
        kwargs['active_tab'] = 'tournaments'
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not has_breaks_permission(request.user, BreaksPermission.EDIT):
            return self.handle_no_permission()
        action = request.POST.get('action')
        if action == 'add_region':
            form = BreakRegionForm(request.POST)
            if form.is_valid():
                region = form.save(commit=False)
                region.season = self.season
                region.save()
                messages.success(request, _("Region %(region)s was added.") % {'region': region.name})
                return redirect('seasonbreaks-tournaments', season_slug=self.season.slug)
            return self.render_to_response(self.get_context_data(region_form=form))
        if action == 'add_tournament':
            form = BreakTournamentForm(request.POST, season=self.season)
            if form.is_valid():
                break_tournament = form.save()
                messages.success(request, _("Tournament %(tournament)s was added.") % {'tournament': break_tournament.tournament})
                return redirect('seasonbreaks-tournaments', season_slug=self.season.slug)
            return self.render_to_response(self.get_context_data(tournament_form=form))
        if action == 'freeze':
            break_tournament = get_object_or_404(BreakTournament, id=request.POST.get('break_tournament'), season=self.season)
            counts = freeze_break_tournament(break_tournament)
            messages.success(request, _("Updated snapshot: %(teams)d teams, %(speakers)d speaker links, %(adjudicators)d adjudicators.") % counts)
            return redirect('seasonbreaks-tournaments', season_slug=self.season.slug)
        return redirect('seasonbreaks-tournaments', season_slug=self.season.slug)


class SeasonTeamsView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/teams.html'

    def get_context_data(self, **kwargs):
        kwargs['teams'] = self.season.teams.select_related('institution', 'region').prefetch_related('links__team')
        kwargs['team_links'] = BreakTeamLink.objects.filter(season=self.season).select_related(
            'team__tournament', 'break_team',
        ).order_by('team__tournament__seq', 'team__short_name')
        kwargs['team_form'] = kwargs.get('team_form') or BreakTeamForm(season=self.season)
        kwargs['active_tab'] = 'teams'
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not has_breaks_permission(request.user, BreaksPermission.EDIT):
            return self.handle_no_permission()
        action = request.POST.get('action')
        if action == 'create_team':
            form = BreakTeamForm(request.POST, season=self.season)
            if form.is_valid():
                team = form.save()
                messages.success(request, _("Season team %(team)s was created.") % {'team': team})
                return redirect('seasonbreaks-teams', season_slug=self.season.slug)
            return self.render_to_response(self.get_context_data(team_form=form))
        if action == 'update_team_link':
            link = get_object_or_404(BreakTeamLink, id=request.POST.get('link'), season=self.season)
            break_team = get_object_or_404(BreakTeam, id=request.POST.get('break_team'), season=self.season)
            link.break_team = break_team
            link.save(update_fields=['break_team'])
            messages.success(request, _("Team link was updated."))
            return redirect('seasonbreaks-teams', season_slug=self.season.slug)
        return redirect('seasonbreaks-teams', season_slug=self.season.slug)


class SeasonSpeakersView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/speakers.html'

    def get_context_data(self, **kwargs):
        kwargs['speakers'] = self.season.speakers.prefetch_related('links__speaker__team')
        kwargs['speaker_links'] = BreakSpeakerLink.objects.filter(season=self.season).select_related(
            'speaker__team__tournament', 'break_speaker',
        ).order_by('speaker__team__tournament__seq', 'speaker__name')
        kwargs['speaker_form'] = kwargs.get('speaker_form') or BreakSpeakerForm(season=self.season)
        kwargs['active_tab'] = 'speakers'
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not has_breaks_permission(request.user, BreaksPermission.EDIT):
            return self.handle_no_permission()
        action = request.POST.get('action')
        if action == 'create_speaker':
            form = BreakSpeakerForm(request.POST, season=self.season)
            if form.is_valid():
                speaker = form.save()
                messages.success(request, _("Season speaker %(speaker)s was created.") % {'speaker': speaker})
                return redirect('seasonbreaks-speakers', season_slug=self.season.slug)
            return self.render_to_response(self.get_context_data(speaker_form=form))
        if action == 'update_speaker_link':
            link = get_object_or_404(BreakSpeakerLink, id=request.POST.get('link'), season=self.season)
            break_speaker = get_object_or_404(self.season.speakers, id=request.POST.get('break_speaker'))
            link.break_speaker = break_speaker
            link.save(update_fields=['break_speaker'])
            messages.success(request, _("Speaker link was updated."))
            return redirect('seasonbreaks-speakers', season_slug=self.season.slug)
        return redirect('seasonbreaks-speakers', season_slug=self.season.slug)


class SeasonQuotasView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/quotas.html'

    def get_context_data(self, **kwargs):
        kwargs['quotas'] = calculate_region_quotas(self.season)
        kwargs['active_tab'] = 'quotas'
        return super().get_context_data(**kwargs)


class SeasonRankingsView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/rankings.html'

    def get_context_data(self, **kwargs):
        rankings = calculate_rankings(self.season)
        kwargs['regions'] = [(region, rankings.get(region.id, [])) for region in self.season.regions.all()]
        kwargs['active_tab'] = 'rankings'
        return super().get_context_data(**kwargs)


class SeasonAdjudicatorsView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/adjudicators.html'

    def get_context_data(self, **kwargs):
        rows = []
        stats = BreakAdjudicatorTournamentStats.objects.filter(
            break_tournament__season=self.season,
        ).select_related('break_adjudicator', 'break_tournament__tournament').order_by('break_adjudicator__name')
        totals = defaultdict(lambda: {
            'chair_count': 0,
            'panellist_count': 0,
            'trainee_count': 0,
            'total_count': 0,
            'details': [],
        })
        adjudicators = {}
        for stat in stats:
            adjudicators[stat.break_adjudicator_id] = stat.break_adjudicator
            row = totals[stat.break_adjudicator_id]
            row['chair_count'] += stat.chair_count
            row['panellist_count'] += stat.panellist_count
            row['trainee_count'] += stat.trainee_count
            row['total_count'] += stat.total_count
            row['details'].append(stat)
        for adjudicator_id, total in totals.items():
            rows.append({'adjudicator': adjudicators[adjudicator_id], **total})
        rows.sort(key=lambda row: (-row['total_count'], row['adjudicator'].name))
        kwargs['rows'] = rows
        kwargs['active_tab'] = 'adjudicators'
        return super().get_context_data(**kwargs)


class BreaksAccessView(BreaksAccessMixin, TemplateView):
    template_name = 'seasonbreaks/access.html'

    def get_context_data(self, **kwargs):
        permissions_by_user = defaultdict(list)
        for permission in GlobalBreaksPermission.objects.select_related('user').order_by('user__username', 'permission'):
            permissions_by_user[permission.user].append(permission.permission)
        kwargs['form'] = kwargs.get('form') or BreaksAccessForm()
        kwargs['access_rows'] = permissions_by_user.items()
        kwargs['active_tab'] = 'access'
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        form = BreaksAccessForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Breaks access updated for %(user)s.") % {'user': user})
            return redirect('seasonbreaks-access')
        return self.render_to_response(self.get_context_data(form=form))
