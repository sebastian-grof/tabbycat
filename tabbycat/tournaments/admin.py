from django.contrib import admin

from utils.admin import ModelAdmin

from .models import Round, ScheduleEvent, Tournament, TournamentCategory


# ==============================================================================
# Tournament
# ==============================================================================

@admin.register(Tournament)
class TournamentAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'homepage_category', 'seq', 'short_name', 'current_round', 'active')
    list_filter = ('homepage_category', 'active')
    ordering = ('homepage_category__seq', 'seq', )


@admin.register(TournamentCategory)
class TournamentCategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'seq', 'public', 'active')
    list_editable = ('parent', 'seq', 'public', 'active')
    list_filter = ('parent', 'public', 'active')
    ordering = ('seq', 'name')


# ==============================================================================
# Round
# ==============================================================================

@admin.register(Round)
class RoundAdmin(ModelAdmin):
    list_display = ('name', 'tournament', 'seq', 'abbreviation', 'stage',
                    'draw_type', 'draw_status', 'feedback_weight', 'silent',
                    'motions_status', 'starts_at', 'completed')
    list_editable = ('feedback_weight', 'silent', 'motions_status', 'completed')
    list_filter = ('tournament', )
    search_fields = ('name', 'seq', 'abbreviation', 'stage', 'draw_type', 'draw_status')
    ordering = ('tournament__slug', 'seq')


@admin.register(ScheduleEvent)
class ScheduleEventAdmin(ModelAdmin):
    list_display = ('tournament', 'title', 'type', 'start_time', 'end_time', 'round')
    list_filter = ('tournament', 'type')
    search_fields = ('title',)
    ordering = ('tournament', 'start_time')
