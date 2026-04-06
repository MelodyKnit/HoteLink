"""apps/operations/apps.py —— 运营应用配置。"""

from django.apps import AppConfig


class OperationsConfig(AppConfig):
    """运营应用注册配置。"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.operations"
    verbose_name = "Operations"
