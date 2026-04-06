"""apps/payments/apps.py —— 支付应用配置。"""

from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """支付应用注册配置。"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payments"
    verbose_name = "Payments"
