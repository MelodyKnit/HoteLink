from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=100)
    target = models.CharField(max_length=100, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.action


class SystemNotice(models.Model):
    TYPE_ORDER = "order"
    TYPE_PAYMENT = "payment"
    TYPE_ACTIVITY = "activity"
    TYPE_SYSTEM = "system"
    TYPE_REVIEW = "review"
    TYPE_CHOICES = [
        (TYPE_ORDER, "订单通知"),
        (TYPE_PAYMENT, "支付通知"),
        (TYPE_ACTIVITY, "活动通知"),
        (TYPE_SYSTEM, "系统通知"),
        (TYPE_REVIEW, "评价通知"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="system_notices")
    notice_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_SYSTEM)
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "System Notice"
        verbose_name_plural = "System Notices"
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.title
