"""
config/settings/dev.py —— 开发环境配置。
继承 base.py 并覆盖开发所需的宽松限制：开启调试模式、允许跨域、放行任意主机。
警告：此配置严禁用于生产节点。
"""
from .base import *

# 开启调试模式：显示详细错误信息
DEBUG = True
# 允许所有跨域请求，方便前后端本地联调
CORS_ALLOW_ALL_ORIGINS = True
# 允许任意主机访问，无需配置具体 IP
ALLOWED_HOSTS = ["*"]
