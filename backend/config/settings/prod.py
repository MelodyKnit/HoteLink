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
# 生产环境默认仅允许在启用开关时暴露 API 文档
ENABLE_API_DOCS = get_bool("ENABLE_API_DOCS", False)
# 若反向代理未正确回传 HTTPS，请先修复代理配置再关闭该开关
SECURE_SSL_REDIRECT = get_bool("DJANGO_SECURE_SSL_REDIRECT", True)
# 开启 HSTS，强制浏览器后续请求继续使用 HTTPS
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
SECURE_HSTS_PRELOAD = get_bool("DJANGO_SECURE_HSTS_PRELOAD", True)
# 仅通过 HTTPS 传输 Session Cookie
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
# 仅通过 HTTPS 传输 CSRF Cookie
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
# 禁止浏览器猜测 MIME 类型（防止内容嗅探攻击）
SECURE_CONTENT_TYPE_NOSNIFF = True
# 禁止嵌入 iframe，防止点击劫持
X_FRAME_OPTIONS = "DENY"
# 约束跨站来源回传的 Referer 粒度，减少敏感路径泄露
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
# 将不同站点上下文隔离，减少窗口引用与资源窃取风险
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
