"""
apps/api/permissions.py —— 自定义 DRF 权限类。

包含辅助函数 get_user_role()，以及 IsAdminRole 权限类（仅允许
酒店管理员或系统管理员访问的接口）。
"""
from rest_framework.permissions import BasePermission


def get_user_role(user) -> str:
    """
    获取用户的角色字符串。

    角色优先级：superuser → 'system_admin'，
    带 profile 的普通用户 → profile.role，
    未登录/无 profile → 空字符串。
    """
    if not user or not user.is_authenticated:
        return ""
    # Django 超级管理员直接返回最高权限
    if getattr(user, "is_superuser", False):
        return "system_admin"
    # 从关联的 UserProfile 读取角色
    profile = getattr(user, "profile", None)
    if profile:
        return profile.role
    return "user"


class IsAdminRole(BasePermission):
    """仅允许 hotel_admin 或 system_admin 访问的 DRF 权限类。"""

    def has_permission(self, request, view) -> bool:
        """检查当前请求用户是否具有管理员角色。"""
        return get_user_role(request.user) in {"hotel_admin", "system_admin"}
