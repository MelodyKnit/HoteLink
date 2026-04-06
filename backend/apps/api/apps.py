"""apps/api/apps.py —— API 应用配置。"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """API Django 应用注册配置。"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api"
    verbose_name = "API"
