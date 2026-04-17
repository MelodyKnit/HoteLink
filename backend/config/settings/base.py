"""
config/settings/base.py —— Django 工程基础配置。

包含所有环境共享的设置项：Installed Apps、中间件、数据库、
REST Framework、JWT、CORS、Celery、日志、AI 等。
开发和生产配置分别由 dev.py / prod.py 导入并覆盖必要的字段。
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
import pymysql

from config.ai import load_ai_settings

# 将 pymysql 注册为 MySQLdb 兼容驱动（Django 默认使用 MySQLdb 接口）
pymysql.install_as_MySQLdb()
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__ = "2.2.1"

# 项目根目录（backend/）
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# 从 .env 文件载入环境变量，开发模式下使用
load_dotenv(BASE_DIR / ".env")


def get_bool(name: str, default: bool = False) -> bool:
    """从环境变量读取布尔值，支持 '1'/'true'/'yes'/'on' 形式。"""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_list(name: str, default: list[str] | None = None) -> list[str]:
    """从环境变量读取逗号分隔的字符串列表，自动去除空白项。"""
    value = os.getenv(name)
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


# 密钥，生产环境必须通过环境变量进行覆盖
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me-please-replace-with-a-long-random-secret")
# 调试模式，生产环境应为 False
DEBUG = get_bool("DJANGO_DEBUG", False)
# 允许访问的主机名列表
ALLOWED_HOSTS = get_list("DJANGO_ALLOWED_HOSTS", ["127.0.0.1", "localhost"])
# 信任的 CSRF 请求来源（包含前端域名）
CSRF_TRUSTED_ORIGINS = get_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])

# 已安装的 App 列表：Django 内置应用 + 第三方和项目自定义 App
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "django_celery_beat",
    "apps.api",
    "apps.users",
    "apps.hotels",
    "apps.bookings",
    "apps.payments",
    "apps.crm",
    "apps.reports",
    "apps.operations",
]

# HTTP 请求处理链：按顺序依次执行
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# 数据库配置：有 DB_HOST 环境变量时使用 MySQL，否则回退到 SQLite（本地加密开发）
db_host = os.getenv("DB_HOST")
if db_host:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "hotelink"),
            "USER": os.getenv("DB_USER", "root"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": db_host,
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# 展示语言和时区
LANGUAGE_CODE = "zh-hans"
# 默认上海时区，可通过环境变量配置
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Shanghai")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "hotelink-default-cache",
    }
}

# REST Framework 全局默认配置：使用 JWT 认证、登录用户才能访问、支持过滤和开放 API 文档
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("API_THROTTLE_ANON", "120/minute"),
        "user": os.getenv("API_THROTTLE_USER", "300/minute"),
        "auth_login": os.getenv("API_THROTTLE_AUTH_LOGIN", "5/minute"),
        "auth_refresh": os.getenv("API_THROTTLE_AUTH_REFRESH", "20/minute"),
        "auth_logout": os.getenv("API_THROTTLE_AUTH_LOGOUT", "30/minute"),
        "system_init": os.getenv("API_THROTTLE_SYSTEM_INIT", "3/hour"),
        "upload": os.getenv("API_THROTTLE_UPLOAD", "20/hour"),
        "ai_user": os.getenv("API_THROTTLE_AI_USER", "30/hour"),
        "ai_admin": os.getenv("API_THROTTLE_AI_ADMIN", "60/hour"),
    },
}

# JWT token 生命周期配置：Access Token 2小时，Refresh Token 7天（可通过环境变量调整）
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "120"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": get_bool("JWT_ROTATE_REFRESH_TOKENS", True),
    "BLACKLIST_AFTER_ROTATION": get_bool("JWT_BLACKLIST_AFTER_ROTATION", True),
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "HoteLink API",
    "DESCRIPTION": "Hotel management system API",
    "VERSION": "1.0.0",
}

ENABLE_API_DOCS = get_bool("ENABLE_API_DOCS", DEBUG)

# CORS 跨域请求允许配置：开发模式下允许所有来源，生产应配置具体域名
CORS_ALLOW_ALL_ORIGINS = get_bool("CORS_ALLOW_ALL_ORIGINS", DEBUG)
CORS_ALLOWED_ORIGINS = get_list("CORS_ALLOWED_ORIGINS", [])

# Redis 缓存地址
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
# Celery 消息代理（任务分发）使用 Redis DB1
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
# Celery 任务结果存储使用 Redis DB2
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/2")
CELERY_TIMEZONE = TIME_ZONE
ORDER_TIMEOUT_SWEEP_INTERVAL_MINUTES = int(os.getenv("ORDER_TIMEOUT_SWEEP_INTERVAL_MINUTES", "5"))
ORDER_TIMEOUT_SWEEP_BATCH_SIZE = int(os.getenv("ORDER_TIMEOUT_SWEEP_BATCH_SIZE", "500"))
ORDER_LIFECYCLE_SWEEP_INTERVAL_MINUTES = int(os.getenv("ORDER_LIFECYCLE_SWEEP_INTERVAL_MINUTES", "5"))
ORDER_LIFECYCLE_SWEEP_BATCH_SIZE = int(os.getenv("ORDER_LIFECYCLE_SWEEP_BATCH_SIZE", "500"))
CELERY_BEAT_SCHEDULE = {
    "order-timeout-sweep": {
        "task": "apps.bookings.tasks.sweep_timeout_unpaid_orders",
        "schedule": timedelta(minutes=max(1, ORDER_TIMEOUT_SWEEP_INTERVAL_MINUTES)),
        "args": (max(1, ORDER_TIMEOUT_SWEEP_BATCH_SIZE),),
    },
    "order-lifecycle-sweep": {
        "task": "apps.bookings.tasks.sweep_order_lifecycle_anomalies",
        "schedule": timedelta(minutes=max(1, ORDER_LIFECYCLE_SWEEP_INTERVAL_MINUTES)),
        "args": (max(1, ORDER_LIFECYCLE_SWEEP_BATCH_SIZE),),
    },
}

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_MB * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_MB * 1024 * 1024

# 日志配置：统一使用控制台输出，格式包含时间戳/级别/模块名；日志级别由 LOG_LEVEL 环境变量控制
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
}

# 在模块加载时立即读取 AI 配置，挂载到 settings.AI_SETTINGS 供全局使用
# 多供应商配置支持：可通过 config.ai.update_ai_settings() 运行时动态切换
AI_SETTINGS = load_ai_settings()
