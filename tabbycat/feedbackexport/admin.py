from django.contrib import admin

from .models import (
    AdjudicatorStatsExportEvent,
    FeedbackExportEvent,
    GlobalFeedbackExportPermission,
    JudgeProfile,
    JudgeProfileLink,
)


@admin.register(GlobalFeedbackExportPermission)
class GlobalFeedbackExportPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission')
    list_filter = ('permission',)
    search_fields = ('user__username', 'user__email')


class JudgeProfileLinkInline(admin.TabularInline):
    model = JudgeProfileLink
    extra = 0
    autocomplete_fields = ('adjudicator',)


@admin.register(JudgeProfile)
class JudgeProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'primary_email', 'external_id', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'primary_email', 'external_id')
    inlines = [JudgeProfileLinkInline]


@admin.register(JudgeProfileLink)
class JudgeProfileLinkAdmin(admin.ModelAdmin):
    list_display = ('profile', 'adjudicator', 'created_at')
    search_fields = ('profile__name', 'adjudicator__name', 'adjudicator__email')
    autocomplete_fields = ('profile', 'adjudicator')


@admin.register(FeedbackExportEvent)
class FeedbackExportEventAdmin(admin.ModelAdmin):
    list_display = ('feedback', 'status', 'attempts', 'last_http_status', 'sent_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('feedback__adjudicator__name', 'idempotency_key', 'last_error')
    readonly_fields = ('payload', 'remote_response')


@admin.register(AdjudicatorStatsExportEvent)
class AdjudicatorStatsExportEventAdmin(admin.ModelAdmin):
    list_display = ('break_tournament', 'status', 'attempts', 'last_http_status', 'sent_at', 'updated_at')
    list_filter = ('status',)
    search_fields = (
        'break_tournament__season__name',
        'break_tournament__tournament__name',
        'break_tournament__tournament__slug',
        'idempotency_key',
        'last_error',
    )
    readonly_fields = ('payload', 'remote_response')
