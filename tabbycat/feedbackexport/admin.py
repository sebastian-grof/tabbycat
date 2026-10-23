from django.contrib import admin

from .models import (
    AdjudicatorStatsExportEvent,
    ExportJob,
    FeedbackExportEvent,
    GlobalFeedbackExportPermission,
)


@admin.register(GlobalFeedbackExportPermission)
class GlobalFeedbackExportPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission')
    list_filter = ('permission',)
    search_fields = ('user__username', 'user__email')


class ReadOnlyExportAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]


@admin.register(ExportJob)
class ExportJobAdmin(ReadOnlyExportAdmin):
    list_display = ('id', 'requested_by', 'status', 'created_at', 'completed_at')
    list_filter = ('status',)


@admin.register(FeedbackExportEvent)
class FeedbackExportEventAdmin(ReadOnlyExportAdmin):
    list_display = ('feedback', 'status', 'attempts', 'last_http_status', 'sent_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('feedback__adjudicator__name', 'idempotency_key', 'last_error')
    readonly_fields = ('payload', 'remote_response')


@admin.register(AdjudicatorStatsExportEvent)
class AdjudicatorStatsExportEventAdmin(ReadOnlyExportAdmin):
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
