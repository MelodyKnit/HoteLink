from rest_framework.response import Response


def api_response(*, data=None, message: str = "success", code: int = 0, status_code: int = 200) -> Response:
    return Response(
        {
            "code": code,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def paginated_response(*, items, page: int, page_size: int, total: int, message: str = "success") -> Response:
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    return api_response(
        data={
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
        message=message,
    )
