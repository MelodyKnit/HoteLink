"""apps/crm/apps.py —— CRM 应用配置。"""

from django.apps import AppConfig


class CrmConfig(AppConfig):
    """CRM 应用注册配置。"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.crm"
    verbose_name = "CRM"
