"""
config/settings/prod.py —— 生产环境配置。
继承 base.py 并加强安全限制：关闭调试模式、强制 HTTPS、
对抗 XSS/CSRF/点击劫持等常见 Web 攻击。
"""
from .base import *

# 关闭调试模式，隐藏内部错误详情
DEBUG = False
# 通知 Django HTTPS 由反向代理转发，确保 request.is_secure() 正确
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# 仅通过 HTTPS 传输 Session Cookie
SESSION_COOKIE_SECURE = True
# 仅通过 HTTPS 传输 CSRF Cookie
CSRF_COOKIE_SECURE = True
# 启用浏览器内建 XSS 过滤器
SECURE_BROWSER_XSS_FILTER = True
# 禁止浏览器猜测 MIME 类型（防止内容嗅探攻击）
SECURE_CONTENT_TYPE_NOSNIFF = True
# 禁止嵌入 iframe，防止点击劫持
X_FRAME_OPTIONS = "DENY"
