from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_USER = "user"
    ROLE_HOTEL_ADMIN = "hotel_admin"
    ROLE_SYSTEM_ADMIN = "system_admin"
    ROLE_CHOICES = [
        (ROLE_USER, "普通用户"),
        (ROLE_HOTEL_ADMIN, "酒店管理员"),
        (ROLE_SYSTEM_ADMIN, "系统管理员"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_DISABLED = "disabled"
    STATUS_LOCKED = "locked"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "正常"),
        (STATUS_DISABLED, "禁用"),
        (STATUS_LOCKED, "锁定"),
    ]

    MEMBER_NORMAL = "normal"
    MEMBER_SILVER = "silver"
    MEMBER_GOLD = "gold"
    MEMBER_PLATINUM = "platinum"
    MEMBER_LEVEL_CHOICES = [
        (MEMBER_NORMAL, "普通会员"),
        (MEMBER_SILVER, "银卡会员"),
        (MEMBER_GOLD, "金卡会员"),
        (MEMBER_PLATINUM, "白金会员"),
    ]

    GENDER_UNKNOWN = "unknown"
    GENDER_MALE = "male"
    GENDER_FEMALE = "female"
    GENDER_CHOICES = [
        (GENDER_UNKNOWN, "未知"),
        (GENDER_MALE, "男"),
        (GENDER_FEMALE, "女"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    nickname = models.CharField(max_length=100, blank=True)
    avatar = models.URLField(blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default=GENDER_UNKNOWN)
    birthday = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default=ROLE_USER)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    member_level = models.CharField(max_length=32, choices=MEMBER_LEVEL_CHOICES, default=MEMBER_NORMAL)
    points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self) -> str:
        return self.nickname or self.user.username
