"""apps/reports/apps.py —— 报表应用配置。"""

from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """报表应用注册配置。"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reports"
    verbose_name = "Reports"
