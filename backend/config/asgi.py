"""
config/asgi.py —— ASGI 应用入口。
暴露符合 ASGI 规范的 `application` 对象，供生产环境 ASGI 服务器
（如 uvicorn、daphne）在部署时使用。
默认使用 config.settings.dev 配置（生产部署时应通过环境变量覆盖）。
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_asgi_application()
