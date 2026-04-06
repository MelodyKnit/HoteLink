"""
config/wsgi.py —— WSGI 应用入口。
暴露符合 WSGI 规范的 `application` 对象，供生产环境 WSGI 服务器
（如 gunicorn）在部署时使用。
默认使用 config.settings.dev 配置（生产部署时应通过环境变量覆盖）。
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# 创建 WSGI 可调用对象，服务器将通过此对象转发 HTTP 请求
application = get_wsgi_application()
