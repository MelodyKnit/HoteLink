"""apps/users/views.py —— users 应用示例接口。"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class UserPlaceholderView(APIView):
    """users 模块占位接口，用于鉴权连通性检查。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """返回 users 模块探活数据。"""
        return Response({"code": 0, "message": "success", "data": {"module": "users"}})
