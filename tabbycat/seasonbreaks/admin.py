from django.contrib import admin

from . import models


@admin.register(models.GlobalBreaksPermission)
class GlobalBreaksPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission')
    list_filter = ('permission',)
    search_fields = ('user__username', 'user__email')


class BreakRegionInline(admin.TabularInline):
    model = models.BreakRegion
    extra = 0


@admin.register(models.BreakSeason)
class BreakSeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'league', 'regional_slots', 'invited_teams', 'effective_regional_slots', 'active')
    list_filter = ('league', 'active')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (BreakRegionInline,)


@admin.register(models.BreakTournament)
class BreakTournamentAdmin(admin.ModelAdmin):
    list_display = ('season', 'tournament', 'region', 'seq', 'frozen_at')
    list_filter = ('season', 'region')
    search_fields = ('tournament__name', 'tournament__short_name', 'tournament__slug')


for model in (
    models.BreakRegion,
    models.BreakTeam,
    models.BreakTeamLink,
    models.BreakSpeaker,
    models.BreakSpeakerLink,
    models.BreakTeamTournamentResult,
    models.BreakSpeakerTournamentParticipation,
    models.BreakAdjudicator,
    models.BreakAdjudicatorLink,
    models.BreakAdjudicatorTournamentStats,
):
    admin.site.register(model)
