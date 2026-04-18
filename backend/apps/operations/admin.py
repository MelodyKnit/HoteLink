"""operations admin 配置模块。"""

from django.contrib import admin
from .models import PlatformConfig, AuditLog, SystemNotice, AICallLog, RuntimeConfig


@admin.register(PlatformConfig)
class PlatformConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "platform_name", "order_auto_cancel_minutes")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "action", "target", "created_at")
    list_filter = ("action",)
    search_fields = ("action", "target")
    readonly_fields = ("user", "action", "target", "detail", "created_at")


@admin.register(SystemNotice)
class SystemNoticeAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "notice_type", "title", "is_read", "created_at")
    list_filter = ("notice_type", "is_read")
    search_fields = ("title", "content")


@admin.register(AICallLog)
class AICallLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "scene", "model", "status", "latency_ms", "created_at")
    list_filter = ("scene", "status")
    search_fields = ("scene",)


@admin.register(RuntimeConfig)
class RuntimeConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "updated_at")
    search_fields = ("key",)

