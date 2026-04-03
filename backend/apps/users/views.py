from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class UserPlaceholderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"code": 0, "message": "success", "data": {"module": "users"}})
