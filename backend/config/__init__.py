"""config 包：Django 项目配置与入口模块。"""

from .celery import app as celery_app

__all__ = ("celery_app",)
