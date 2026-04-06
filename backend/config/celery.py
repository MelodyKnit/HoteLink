"""
config/celery.py —— Celery 异步任务队列配置。
创建 Celery 应用实例，从 Django settings 中读取以 CELERY_ 为前缀的配置项，
并自动发现各 Django App 内定义的 tasks.py 任务模块。
"""
import os

from celery import Celery

# 确保 worker 进程启动时能加载 Django 配置
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# 创建 Celery 实例，项目名称 hotelink 用于区分任务和队列前缀
app = Celery("hotelink")

# 从 Django settings 中读取所有 CELERY_* 配置项（如 broker、backend、队列等）
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动搜索并注册所有已安装 App 中的 tasks.py 任务
app.autodiscover_tasks()
