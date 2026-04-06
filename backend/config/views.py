"""
config/views.py —— 全局通用视图。
目前仅包含健康检查端点，供负载均衡器、监控平台探活使用。
"""
from django.http import JsonResponse


def health_check(_request):
    """健康检查视图，返回服务名称和运行状态，始终响应 HTTP 200。"""
    return JsonResponse(
        {
            "code": 0,
            "message": "success",
            "data": {
                "service": "hotelink-backend",
                "status": "ok",
            },
        }
    )
