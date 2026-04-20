"""apps/api/authentication.py —— 自定义 JWT 认证类，额外校验用户账号状态。"""

from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication


class ActiveUserJWTAuthentication(JWTAuthentication):
    """在标准 JWT 认证基础上，拒绝已被禁用或锁定的用户。"""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        profile = getattr(user, "profile", None)
        if profile and profile.status != "active":
            raise exceptions.AuthenticationFailed("账号已被禁用或锁定，请联系管理员")
        return user
