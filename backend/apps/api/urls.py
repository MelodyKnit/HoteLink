from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class ApiRootView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "name": "HoteLink API",
                    "version": "v1",
                    "user_api_base": "/api/v1/user/",
                    "admin_api_base": "/api/v1/admin/",
                },
            }
        )


urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
]
