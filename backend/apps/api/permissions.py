from rest_framework.permissions import BasePermission


def get_user_role(user) -> str:
    if not user or not user.is_authenticated:
        return ""
    if getattr(user, "is_superuser", False):
        return "system_admin"
    profile = getattr(user, "profile", None)
    if profile:
        return profile.role
    return "user"


class IsAdminRole(BasePermission):
    def has_permission(self, request, view) -> bool:
        return get_user_role(request.user) in {"hotel_admin", "system_admin"}
