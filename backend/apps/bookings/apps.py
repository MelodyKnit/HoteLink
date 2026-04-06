"""apps/bookings/apps.py —— 订单应用配置。"""

from django.apps import AppConfig


class BookingsConfig(AppConfig):
    """订单应用注册配置。"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bookings"
    verbose_name = "Bookings"
