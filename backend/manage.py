#!/usr/bin/env python
"""
manage.py —— Django 项目管理命令入口。
提供 runserver、migrate、createsuperuser 等所有 Django 管理命令的统一入口点。
默认使用 config.settings.dev 配置（可通过环境变量 DJANGO_SETTINGS_MODULE 覆盖）。
"""
import os
import sys


def main() -> None:
    """设置默认配置模块并转发命令行参数给 Django 管理框架。"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your "
            "PYTHONPATH environment variable? Did you forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
