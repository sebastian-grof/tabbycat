from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic import TemplateView

from .forms import (
    BreakAdjudicatorForm,
    BreakRegionForm,
    BreakSeasonForm,
    BreakSpeakerForm,
    BreakTeamForm,
    BreakTournamentForm,
    BreaksAccessForm,
)
from .models import (
    BreakAdjudicator,
    BreakAdjudicatorLink,
    BreakAdjudicatorTournamentStats,
    BreaksPermission,
    BreakRegion,
    BreakSeason,
    BreakSpeakerLink,
    BreakTeam,
    BreakTeamLink,
    BreakTournament,
    GlobalBreaksPermission,
)
from .permissions import has_breaks_permission
from .services import (
    calculate_rankings,
    calculate_region_quotas,
    freeze_break_tournament,
    prune_all_unused_break_identities,
    prune_unused_break_identities,
    season_summary,
)


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
        kwargs['season_nav_groups'] = season_nav_groups(self.season)
        return super().get_context_data(**kwargs)


def season_tabs(season):
    return [
        (_("Overview"), reverse('seasonbreaks-season-overview', kwargs={'season_slug': season.slug}), 'overview'),
        (_("Tournaments"), reverse('seasonbreaks-tournaments', kwargs={'season_slug': season.slug}), 'tournaments'),
        (_("Identities"), reverse('seasonbreaks-identities', kwargs={'season_slug': season.slug}), 'identities'),
        (_("Teams"), reverse('seasonbreaks-teams', kwargs={'season_slug': season.slug}), 'teams'),
        (_("Speakers"), reverse('seasonbreaks-speakers', kwargs={'season_slug': season.slug}), 'speakers'),
        (_("Quotas"), reverse('seasonbreaks-quotas', kwargs={'season_slug': season.slug}), 'quotas'),
        (_("Rankings"), reverse('seasonbreaks-rankings', kwargs={'season_slug': season.slug}), 'rankings'),
        (_("Adjudicators"), reverse('seasonbreaks-adjudicators', kwargs={'season_slug': season.slug}), 'adjudicators'),
        (_("Access"), reverse('seasonbreaks-access'), 'access'),
    ]


def season_nav_groups(season):
    return [
        ('season', _("Season"), [
            (_("Overview"), reverse('seasonbreaks-season-overview', kwargs={'season_slug': season.slug}), 'overview',
                _("Status, frozen data and quota snapshot")),
            (_("Tournaments"), reverse('seasonbreaks-tournaments', kwargs={'season_slug': season.slug}), 'tournaments',
                _("Regions, source tournaments and snapshots")),
        ]),
        ('identities', _("Identities"), [
            (_("Identity hub"), reverse('seasonbreaks-identities', kwargs={'season_slug': season.slug}), 'identities',
                _("Choose teams, speakers or adjudicators")),
            (_("Teams"), reverse('seasonbreaks-teams', kwargs={'season_slug': season.slug}), 'teams',
                _("Season team identities")),
            (_("Speakers"), reverse('seasonbreaks-speakers', kwargs={'season_slug': season.slug}), 'speakers',
                _("Season speaker identities")),
        ]),
        ('qualification', _("Qualification"), [
            (_("Quotas"), reverse('seasonbreaks-quotas', kwargs={'season_slug': season.slug}), 'quotas',
                _("Regional slot calculation")),
            (_("Rankings"), reverse('seasonbreaks-rankings', kwargs={'season_slug': season.slug}), 'rankings',
                _("Qualified teams and eligibility")),
        ]),
        ('people', _("People"), [
            (_("Adjudicators"), reverse('seasonbreaks-adjudicators', kwargs={'season_slug': season.slug}), 'adjudicators',
                _("Chair, panel and trainee totals")),
        ]),
        ('access', _("Access"), [
            (_("Permissions"), reverse('seasonbreaks-access'), 'access', _("Global Breaks permissions")),
        ]),
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
        kwargs['season_form'] = kwargs.get('season_form') or BreakSeasonForm(instance=self.season)
        kwargs['active_tab'] = 'overview'
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not has_breaks_permission(request.user, BreaksPermission.EDIT):
            return self.handle_no_permission()
        form = BreakSeasonForm(request.POST, instance=self.season)
        if form.is_valid():
            season = form.save()
            messages.success(request, _("Break season settings were updated."))
            return redirect('seasonbreaks-season-overview', season_slug=season.slug)
        return self.render_to_response(self.get_context_data(season_form=form))


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
        if action == 'update_tournament_type':
            break_tournament = get_object_or_404(BreakTournament, id=request.POST.get('break_tournament'), season=self.season)
            break_tournament.counts_for_break = request.POST.get('counts_for_break') == '1'
            break_tournament.save(update_fields=['counts_for_break'])
            if not break_tournament.counts_for_break:
                team_identity_ids = list(BreakTeamLink.objects.filter(
                    season=self.season, team__tournament=break_tournament.tournament,
                ).values_list('break_team_id', flat=True).distinct())
                speaker_identity_ids = list(BreakSpeakerLink.objects.filter(
                    season=self.season, speaker__team__tournament=break_tournament.tournament,
                ).values_list('break_speaker_id', flat=True).distinct())
                break_tournament.team_results.all().delete()
                break_tournament.speaker_participations.all().delete()
                BreakTeamLink.objects.filter(
                    season=self.season, team__tournament=break_tournament.tournament,
                ).delete()
                BreakSpeakerLink.objects.filter(
                    season=self.season, speaker__team__tournament=break_tournament.tournament,
                ).delete()
                prune_unused_break_identities(
                    self.season, team_ids=team_identity_ids, speaker_ids=speaker_identity_ids,
                )
            messages.success(request, _("Tournament type was updated."))
            return redirect('seasonbreaks-tournaments', season_slug=self.season.slug)
        if action == 'remove_tournament':
            break_tournament = get_object_or_404(BreakTournament, id=request.POST.get('break_tournament'), season=self.season)
            tournament = break_tournament.tournament
            team_identity_ids = list(BreakTeamLink.objects.filter(
                season=self.season, team__tournament=tournament,
            ).values_list('break_team_id', flat=True).distinct())
            speaker_identity_ids = list(BreakSpeakerLink.objects.filter(
                season=self.season, speaker__team__tournament=tournament,
            ).values_list('break_speaker_id', flat=True).distinct())
            adjudicator_identity_ids = list(BreakAdjudicatorLink.objects.filter(
                season=self.season, adjudicator__tournament=tournament,
            ).values_list('break_adjudicator_id', flat=True).distinct())
            BreakTeamLink.objects.filter(season=self.season, team__tournament=tournament).delete()
            BreakSpeakerLink.objects.filter(season=self.season, speaker__team__tournament=tournament).delete()
            BreakAdjudicatorLink.objects.filter(season=self.season, adjudicator__tournament=tournament).delete()
            break_tournament.delete()
            prune_unused_break_identities(
                self.season, team_ids=team_identity_ids, speaker_ids=speaker_identity_ids,
                adjudicator_ids=adjudicator_identity_ids,
            )
            messages.success(request, _("Tournament %(tournament)s was removed from this Breaks season.") % {'tournament': tournament})
            return redirect('seasonbreaks-tournaments', season_slug=self.season.slug)
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
        kwargs['active_tab'] = 'teams'
        return super().get_context_data(**kwargs)


def _group_links_by_source_tournament(links, tournament_getter, shared_title):
    groups = []
    index = {}
    for link in links:
        tournament = tournament_getter(link)
        source_key = str(tournament.pk) if tournament else 'shared'
        if source_key not in index:
            group = {
                'source_key': source_key,
                'title': str(tournament) if tournament else shared_title,
                'tournament': tournament,
                'links': [],
            }
            index[source_key] = group
            groups.append(group)
        index[source_key]['links'].append(link)
    return groups


def _selected_source_group(request, groups):
    source = request.POST.get('source') or request.GET.get('source')
    if not source and len(groups) == 1:
        source = groups[0]['source_key']
    selected_group = next((group for group in groups if group['source_key'] == source), None)
    return source, selected_group


def _redirect_to_identity_category(view_name, season, source=None):
    url = reverse(view_name, kwargs={'season_slug': season.slug})
    if source:
        url = "%s?source=%s" % (url, source)
    return redirect(url)


class SeasonIdentitiesView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/identities.html'

    def get_context_data(self, **kwargs):
        kwargs['team_identity_count'] = self.season.teams.count()
        kwargs['speaker_identity_count'] = self.season.speakers.count()
        kwargs['adjudicator_identity_count'] = self.season.adjudicators.count()
        kwargs['team_link_count'] = BreakTeamLink.objects.filter(season=self.season).count()
        kwargs['speaker_link_count'] = BreakSpeakerLink.objects.filter(season=self.season).count()
        kwargs['adjudicator_link_count'] = BreakAdjudicatorLink.objects.filter(season=self.season).count()
        kwargs['active_tab'] = 'identities'
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not has_breaks_permission(request.user, BreaksPermission.EDIT):
            return self.handle_no_permission()
        if request.POST.get('action') == 'cleanup_orphan_identities':
            deleted = prune_all_unused_break_identities(self.season)
            messages.success(request, _(
                "Cleaned stale identities: %(teams)d teams, %(speakers)d speakers, %(adjudicators)d adjudicators."
            ) % deleted)
        return redirect('seasonbreaks-identities', season_slug=self.season.slug)


class SeasonTeamIdentitiesView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/identities_teams.html'

    def get_context_data(self, **kwargs):
        links = BreakTeamLink.objects.filter(season=self.season).select_related(
            'team__tournament', 'break_team',
        ).order_by('team__tournament__seq', 'team__tournament__name', 'team__short_name')
        source_groups = _group_links_by_source_tournament(
            links, lambda link: link.team.tournament, _("Unknown tournament"),
        )
        selected_source, selected_group = _selected_source_group(self.request, source_groups)
        kwargs['teams'] = self.season.teams.select_related('institution', 'region').order_by('name')
        kwargs['source_groups'] = source_groups
        kwargs['selected_source'] = selected_source
        kwargs['selected_group'] = selected_group
        kwargs['team_form'] = kwargs.get('team_form') or BreakTeamForm(season=self.season)
        kwargs['active_tab'] = 'identities'
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
                return _redirect_to_identity_category(
                    'seasonbreaks-identities-teams', self.season, request.POST.get('source'),
                )
            return self.render_to_response(self.get_context_data(team_form=form))
        if action == 'update_team_link':
            link = get_object_or_404(BreakTeamLink, id=request.POST.get('link'), season=self.season)
            break_team = get_object_or_404(BreakTeam, id=request.POST.get('break_team'), season=self.season)
            link.break_team = break_team
            link.save(update_fields=['break_team'])
            messages.success(request, _("Team link was updated."))
            return _redirect_to_identity_category(
                'seasonbreaks-identities-teams', self.season, request.POST.get('source'),
            )
        return _redirect_to_identity_category('seasonbreaks-identities-teams', self.season, request.POST.get('source'))


class SeasonSpeakerIdentitiesView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/identities_speakers.html'

    def get_context_data(self, **kwargs):
        links = BreakSpeakerLink.objects.filter(season=self.season).select_related(
            'speaker__team__tournament', 'speaker__team', 'break_speaker',
        ).order_by('speaker__team__tournament__seq', 'speaker__team__tournament__name', 'speaker__name')
        source_groups = _group_links_by_source_tournament(
            links, lambda link: link.speaker.team.tournament, _("Unknown tournament"),
        )
        selected_source, selected_group = _selected_source_group(self.request, source_groups)
        kwargs['speakers'] = self.season.speakers.order_by('name')
        kwargs['source_groups'] = source_groups
        kwargs['selected_source'] = selected_source
        kwargs['selected_group'] = selected_group
        kwargs['speaker_form'] = kwargs.get('speaker_form') or BreakSpeakerForm(season=self.season)
        kwargs['active_tab'] = 'identities'
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
                return _redirect_to_identity_category(
                    'seasonbreaks-identities-speakers', self.season, request.POST.get('source'),
                )
            return self.render_to_response(self.get_context_data(speaker_form=form))
        if action == 'update_speaker_link':
            link = get_object_or_404(BreakSpeakerLink, id=request.POST.get('link'), season=self.season)
            break_speaker = get_object_or_404(self.season.speakers, id=request.POST.get('break_speaker'))
            link.break_speaker = break_speaker
            link.save(update_fields=['break_speaker'])
            messages.success(request, _("Speaker link was updated."))
            return _redirect_to_identity_category(
                'seasonbreaks-identities-speakers', self.season, request.POST.get('source'),
            )
        return _redirect_to_identity_category('seasonbreaks-identities-speakers', self.season, request.POST.get('source'))


class SeasonAdjudicatorIdentitiesView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/identities_adjudicators.html'

    def get_context_data(self, **kwargs):
        links = BreakAdjudicatorLink.objects.filter(season=self.season).select_related(
            'adjudicator__tournament', 'adjudicator__institution', 'break_adjudicator',
        ).order_by('adjudicator__tournament__seq', 'adjudicator__tournament__name', 'adjudicator__name')
        source_groups = _group_links_by_source_tournament(
            links, lambda link: link.adjudicator.tournament, _("Shared adjudicators"),
        )
        selected_source, selected_group = _selected_source_group(self.request, source_groups)
        kwargs['adjudicators'] = self.season.adjudicators.select_related('institution').order_by('name')
        kwargs['source_groups'] = source_groups
        kwargs['selected_source'] = selected_source
        kwargs['selected_group'] = selected_group
        kwargs['adjudicator_form'] = kwargs.get('adjudicator_form') or BreakAdjudicatorForm(season=self.season)
        kwargs['active_tab'] = 'identities'
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not has_breaks_permission(request.user, BreaksPermission.EDIT):
            return self.handle_no_permission()
        action = request.POST.get('action')
        if action == 'create_adjudicator':
            form = BreakAdjudicatorForm(request.POST, season=self.season)
            if form.is_valid():
                adjudicator = form.save()
                messages.success(request, _("Season adjudicator %(adjudicator)s was created.") % {'adjudicator': adjudicator})
                return _redirect_to_identity_category(
                    'seasonbreaks-identities-adjudicators', self.season, request.POST.get('source'),
                )
            return self.render_to_response(self.get_context_data(adjudicator_form=form))
        if action == 'update_adjudicator_link':
            link = get_object_or_404(BreakAdjudicatorLink, id=request.POST.get('link'), season=self.season)
            break_adjudicator = get_object_or_404(BreakAdjudicator, id=request.POST.get('break_adjudicator'), season=self.season)
            link.break_adjudicator = break_adjudicator
            link.save(update_fields=['break_adjudicator'])
            messages.success(request, _("Adjudicator link was updated."))
            return _redirect_to_identity_category(
                'seasonbreaks-identities-adjudicators', self.season, request.POST.get('source'),
            )
        return _redirect_to_identity_category(
            'seasonbreaks-identities-adjudicators', self.season, request.POST.get('source'),
        )


class SeasonSpeakersView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/speakers.html'

    def get_context_data(self, **kwargs):
        kwargs['speakers'] = self.season.speakers.prefetch_related('links__speaker__team')
        kwargs['active_tab'] = 'speakers'
        return super().get_context_data(**kwargs)


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
        regions = []
        for region in self.season.regions.all():
            rows = rankings.get(region.id, [])
            regions.append({
                'region': region,
                'rows': rows,
                'eligible_rows': [row for row in rows if row['eligible']],
            })
        kwargs['regions'] = regions
        kwargs['active_tab'] = 'rankings'
        return super().get_context_data(**kwargs)


class SeasonRegionRankingsView(SeasonMixin, TemplateView):
    template_name = 'seasonbreaks/ranking_region.html'

    def get_context_data(self, **kwargs):
        self.region = get_object_or_404(BreakRegion, season=self.season, id=self.kwargs['region_id'])
        rankings = calculate_rankings(self.season)
        kwargs['region'] = self.region
        kwargs['rows'] = rankings.get(self.region.id, [])
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
