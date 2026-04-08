"""apps/operations/models.py —— 审计日志、系统通知与平台配置模型。"""

from django.conf import settings
from django.db import models


class PlatformConfig(models.Model):
    """平台配置单例模型，存储全局系统设置。"""
    platform_name = models.CharField(max_length=100, default="HoteLink 酒店管理系统")
    admin_name = models.CharField(max_length=100, default="HoteLink 管理端")
    support_phone = models.CharField(max_length=30, default="400-000-0000")
    order_auto_cancel_minutes = models.PositiveIntegerField(default=30)

    class Meta:
        verbose_name = "Platform Config"
        verbose_name_plural = "Platform Configs"

    def __str__(self) -> str:
        return self.platform_name

    @classmethod
    def load(cls) -> "PlatformConfig":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class AuditLog(models.Model):
    """审计日志模型，记录关键操作事件。"""
    user_id: int | None
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
    """系统通知模型，向用户推送站内消息。"""
    TYPE_ORDER = "order"
    TYPE_PAYMENT = "payment"
    TYPE_ACTIVITY = "activity"
    TYPE_SYSTEM = "system"
    TYPE_REVIEW = "review"
    TYPE_MEMBER = "member"
    TYPE_COUPON = "coupon"
    TYPE_CHOICES = [
        (TYPE_ORDER, "订单通知"),
        (TYPE_PAYMENT, "支付通知"),
        (TYPE_ACTIVITY, "活动通知"),
        (TYPE_SYSTEM, "系统通知"),
        (TYPE_REVIEW, "评价通知"),
        (TYPE_MEMBER, "会员通知"),
        (TYPE_COUPON, "优惠券通知"),
    ]

    user_id: int
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


class AICallLog(models.Model):
    """AI 调用日志模型，记录每次 LLM 调用的元数据和费用估算。"""
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_TIMEOUT = "timeout"
    STATUS_QUOTA_EXCEEDED = "quota_exceeded"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "成功"),
        (STATUS_FAILED, "失败"),
        (STATUS_TIMEOUT, "超时"),
        (STATUS_QUOTA_EXCEEDED, "超额"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="ai_call_logs",
    )
    scene = models.CharField(max_length=50, help_text="AI 使用场景标识")
    provider = models.CharField(max_length=50, help_text="AI 供应商名称")
    model = models.CharField(max_length=100, help_text="使用的模型名称")
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=6, default=0, help_text="估算费用（元）")
    latency_ms = models.PositiveIntegerField(default=0, help_text="响应延迟（毫秒）")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    error_message = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI Call Log"
        verbose_name_plural = "AI Call Logs"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.scene} / {self.provider} / {self.status}"
