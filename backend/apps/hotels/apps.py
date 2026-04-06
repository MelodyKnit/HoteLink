"""apps/hotels/apps.py —— 酒店应用配置。"""

from django.apps import AppConfig


class HotelsConfig(AppConfig):
    """酒店应用注册配置。"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.hotels"
    verbose_name = "Hotels"
