from django.contrib import admin

from .models import AuditLog, District, Mahalla, Notification, Region, Report


class DistrictInline(admin.TabularInline):
    model = District
    extra = 0


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    inlines = [DistrictInline]


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ["name", "region"]
    list_filter = ["region"]
    search_fields = ["name"]


@admin.register(Mahalla)
class MahallaAdmin(admin.ModelAdmin):
    list_display = ["name", "district"]
    list_filter = ["district__region"]
    search_fields = ["name", "district__name"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["id", "reason", "target_label", "reporter", "status", "created_at"]
    list_filter = ["status", "reason"]
    readonly_fields = ["reporter", "target_user", "target_service", "reason", "comment", "created_at"]
    fields = ["reporter", "target_user", "target_service", "reason", "comment", "status", "admin_note", "created_at"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "message", "is_read", "created_at"]
    list_filter = ["is_read"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "actor", "action", "object_type", "object_id", "ip_address"]
    list_filter = ["action"]
    search_fields = ["action", "actor__phone"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
