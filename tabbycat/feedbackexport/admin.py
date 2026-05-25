from django.contrib import admin

from .models import (
    AdjudicatorStatsExportEvent,
    FeedbackExportEvent,
    GlobalFeedbackExportPermission,
)


@admin.register(GlobalFeedbackExportPermission)
class GlobalFeedbackExportPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission')
    list_filter = ('permission',)
    search_fields = ('user__username', 'user__email')


@admin.register(FeedbackExportEvent)
class FeedbackExportEventAdmin(admin.ModelAdmin):
    list_display = ('feedback', 'status', 'attempts', 'last_http_status', 'sent_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('feedback__adjudicator__name', 'idempotency_key', 'last_error')
    readonly_fields = ('payload', 'remote_response')


@admin.register(AdjudicatorStatsExportEvent)
class AdjudicatorStatsExportEventAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'source_tournament_id', 'break_tournament', 'status', 'attempts', 'last_http_status', 'sent_at', 'updated_at')
    list_filter = ('status',)
    search_fields = (
        'tournament__name',
        'tournament__slug',
        'source_tournament_name',
        'source_tournament_slug',
        'break_tournament__season__name',
        'break_tournament__tournament__name',
        'break_tournament__tournament__slug',
        'idempotency_key',
        'last_error',
    )
    readonly_fields = ('payload', 'remote_response')
