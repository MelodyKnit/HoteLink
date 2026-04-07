"""apps/users/models.py —— 用户档案扩展模型。"""

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """用户扩展资料模型，承载角色、状态、会员等级与积分信息。"""
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
    MEMBER_DIAMOND = "diamond"
    MEMBER_LEVEL_CHOICES = [
        (MEMBER_NORMAL, "普通会员"),
        (MEMBER_SILVER, "银卡会员"),
        (MEMBER_GOLD, "金卡会员"),
        (MEMBER_PLATINUM, "铂金会员"),
        (MEMBER_DIAMOND, "钻石会员"),
    ]

    # 会员等级积分阈值（每消费10元=1积分）
    MEMBER_THRESHOLDS = {
        MEMBER_NORMAL: 0,
        MEMBER_SILVER: 1000,
        MEMBER_GOLD: 10000,
        MEMBER_PLATINUM: 100000,
        MEMBER_DIAMOND: 1000000,
    }

    # 会员折扣率（下单时自动折扣）
    MEMBER_DISCOUNT_RATE = {
        MEMBER_NORMAL: 1.00,
        MEMBER_SILVER: 0.98,
        MEMBER_GOLD: 0.95,
        MEMBER_PLATINUM: 0.92,
        MEMBER_DIAMOND: 0.88,
    }

    # 会员积分倍率（消费获取积分的倍率）
    MEMBER_POINTS_MULTIPLIER = {
        MEMBER_NORMAL: 1.0,
        MEMBER_SILVER: 1.2,
        MEMBER_GOLD: 1.5,
        MEMBER_PLATINUM: 2.0,
        MEMBER_DIAMOND: 3.0,
    }

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

    def compute_level(self) -> str:
        """根据当前积分计算应有的会员等级。"""
        level = self.MEMBER_NORMAL
        for lv, threshold in sorted(self.MEMBER_THRESHOLDS.items(), key=lambda x: x[1]):
            if self.points >= threshold:
                level = lv
        return level

    def refresh_level(self) -> bool:
        """根据积分刷新会员等级，返回是否发生了升级。"""
        new_level = self.compute_level()
        if new_level != self.member_level:
            self.member_level = new_level
            self.save(update_fields=["member_level", "updated_at"])
            return True
        return False

    @property
    def discount_rate(self) -> float:
        return self.MEMBER_DISCOUNT_RATE.get(self.member_level, 1.0)

    @property
    def points_multiplier(self) -> float:
        return self.MEMBER_POINTS_MULTIPLIER.get(self.member_level, 1.0)
