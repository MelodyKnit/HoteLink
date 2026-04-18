"""payments admin 配置模块。"""

from django.contrib import admin
from .models import PaymentRecord


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "payment_no", "order_id", "method", "status", "amount", "paid_at", "created_at")
    list_filter = ("status", "method")
    search_fields = ("payment_no", "order__order_no")
    readonly_fields = ("payment_no", "order", "method", "amount", "paid_at", "created_at")

