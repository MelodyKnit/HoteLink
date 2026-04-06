"""apps/users/apps.py —— 用户应用配置。"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """用户应用注册配置。"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    verbose_name = "Users"
