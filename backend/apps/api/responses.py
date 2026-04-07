"""
apps/api/responses.py —— 统一响应格式工具函数。

所有 API 接口均应使用这里的工具函数返回响应，保证前后端数据形式一致。
"""
from rest_framework.response import Response


def api_response(*, data=None, message: str = "success", code: int = 0, status_code: int = 200) -> Response:
    """
    构造统一格式的 JSON 响应。

    Args:
        data:        返回给客户端的数据载荷，默认 None。
        message:     描述性文字提示，默认 'success'。
        code:        业务状态码，0 表示成功，非 0 表示各类错误。
        status_code: HTTP 状态码，默认 200。

    Returns:
        包含 {code, message, data} 结构的 DRF Response 对象。
    """
    return Response(
        {
            "code": code,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def paginated_response(*, items, page: int, page_size: int, total: int, message: str = "success", extra: dict | None = None) -> Response:
    """
    构造分页列表响应。

    Args:
        items:     当前页数据列表（已序列化）。
        page:      当前页码（1 起）。
        page_size: 每页条数。
        total:     总条数。
        message:   可选的成功提示。
        extra:     可选的额外字段，会合并进 data 中。

    Returns:
        包含 {items, page, page_size, total, total_pages} 分页信息的 api_response。
    """
    # 向上整除计算总页数
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    data = {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }
    if extra:
        data.update(extra)
    return api_response(
        data=data,
        message=message,
    )
