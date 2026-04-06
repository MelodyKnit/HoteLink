"""
config/urls.py —— 项目根路由配置。

路由分配规则：
  health/       → 健康检查接口
  superadmin/   → Django 自带后台管理页面
  api/v1/       → 所有业务 REST API（转发至 apps.api.urls）
  schema/       → OpenAPI 3.0 路径元数据下载（drf-spectacular）
  docs/         → Swagger UI 交互文档
  redoc/        → ReDoc 验证文档
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from config.views import health_check

urlpatterns = [
    # 远程健康探测，返回服务状态 JSON
    path("health/", health_check, name="health-check"),
    # Django 原生后台管理入口（仅内部运维使用）
    path("superadmin/", admin.site.urls),
    # 全部业务 REST API，由 apps/api/urls.py 细分路由
    path("api/v1/", include("apps.api.urls")),
    # OpenAPI 配置文档（YAML/JSON 格式）下载
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI: 浏览器可视化地调试 API
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # ReDoc: 更简洁的静态 API 文档页
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
