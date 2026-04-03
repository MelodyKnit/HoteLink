from django.http import JsonResponse


def health_check(_request):
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
