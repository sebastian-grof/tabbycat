from django.contrib import admin

from .models import GlobalConverterPermission


@admin.register(GlobalConverterPermission)
class GlobalConverterPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission')
    list_filter = ('permission',)
    search_fields = ('user__username', 'user__email')
