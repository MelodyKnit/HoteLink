"""
apps/api/permissions.py —— 自定义 DRF 权限类。

包含辅助函数 get_user_role()，以及权限类：
- IsActiveUser：检查用户 profile.status 为 active，被禁用/锁定用户立即拒绝。
- IsAdminRole：允许 hotel_admin 或 system_admin 访问。
- IsSystemAdminRole：仅允许 system_admin 访问（系统核心/破坏性操作）。
"""
from rest_framework.permissions import BasePermission


def _get_profile_status(user) -> str:
    """获取用户的 profile.status，superuser 始终视为 active。"""
    if not user or not user.is_authenticated:
        return ""
    if getattr(user, "is_superuser", False):
        return "active"
    profile = getattr(user, "profile", None)
    return getattr(profile, "status", "active") if profile else "active"


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


class IsActiveUser(BasePermission):
    """检查用户账号是否处于 active 状态，被禁用/锁定的用户即使持有有效 JWT 也会被拒绝。"""
    message = "账号已被禁用或锁定，请联系管理员"

    def has_permission(self, request, view) -> bool:
        return _get_profile_status(request.user) == "active"


class IsAdminRole(BasePermission):
    """仅允许 hotel_admin 或 system_admin 访问的 DRF 权限类。"""

    def has_permission(self, request, view) -> bool:
        """检查当前请求用户是否具有管理员角色且账号状态正常。"""
        if _get_profile_status(request.user) != "active":
            return False
        return get_user_role(request.user) in {"hotel_admin", "system_admin"}


class IsSystemAdminRole(BasePermission):
    """仅允许 system_admin 访问的 DRF 权限类，用于系统核心或破坏性操作。"""

    def has_permission(self, request, view) -> bool:
        """检查当前请求用户是否为系统管理员且账号状态正常。"""
        if _get_profile_status(request.user) != "active":
            return False
        return get_user_role(request.user) == "system_admin"
