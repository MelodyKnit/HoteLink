"""apps/crm/models.py —— CRM 相关数据模型。"""

from django.conf import settings
from django.db import models


class CustomerProfile(models.Model):
    """客户档案模型。"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    full_name = models.CharField(max_length=120)
    mobile = models.CharField(max_length=20, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"

    def __str__(self) -> str:
        return self.full_name


class FavoriteHotel(models.Model):
    """用户收藏酒店关系模型。"""
    user_id: int
    hotel_id: int
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_hotels")
    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Favorite Hotel"
        verbose_name_plural = "Favorite Hotels"
        unique_together = ("user", "hotel")
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.user_id}-{self.hotel_id}"


class Review(models.Model):
    """订单评价模型。"""
    order_id: int
    user_id: int
    hotel_id: int
    order = models.OneToOneField("bookings.BookingOrder", on_delete=models.CASCADE, related_name="review")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="reviews")
    score = models.PositiveSmallIntegerField(default=5)
    content = models.TextField()
    images = models.JSONField(default=list, blank=True, help_text="评价图片URL列表")
    reply_content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.hotel_id}-{self.score}"


class PointsLog(models.Model):
    """积分变动日志模型。"""
    TYPE_CONSUME_REWARD = "consume_reward"
    TYPE_REVIEW_REWARD = "review_reward"
    TYPE_COUPON_EXCHANGE = "coupon_exchange"
    TYPE_ADMIN_ADJUST = "admin_adjust"
    TYPE_LEVEL_UP_GIFT = "level_up_gift"
    TYPE_CHOICES = [
        (TYPE_CONSUME_REWARD, "消费奖励"),
        (TYPE_REVIEW_REWARD, "评价奖励"),
        (TYPE_COUPON_EXCHANGE, "积分兑券"),
        (TYPE_ADMIN_ADJUST, "管理员调整"),
        (TYPE_LEVEL_UP_GIFT, "升级礼包"),
    ]

    user_id: int
    order_id: int
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="points_logs")
    log_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    points = models.IntegerField(help_text="正值为获得，负值为消耗")
    balance = models.PositiveIntegerField(help_text="变动后积分余额")
    description = models.CharField(max_length=200)
    order = models.ForeignKey("bookings.BookingOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="points_logs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Points Log"
        verbose_name_plural = "Points Logs"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.user_id} {self.points:+d} ({self.log_type})"


class CouponTemplate(models.Model):
    """优惠券模板，管理员创建，用户可领取。"""
    TYPE_CASH = "cash"
    TYPE_DISCOUNT = "discount"
    TYPE_CHOICES = [
        (TYPE_CASH, "满减券"),
        (TYPE_DISCOUNT, "折扣券"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "有效"),
        (STATUS_INACTIVE, "已下架"),
    ]

    name = models.CharField(max_length=100)
    coupon_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CASH)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="满减金额（cash类型时使用）")
    discount = models.DecimalField(max_digits=3, decimal_places=1, default=10, help_text="折扣值如9.5表示95折（discount类型时使用）")
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="最低消费门槛，0表示无门槛")
    total_count = models.PositiveIntegerField(default=100, help_text="总发行量")
    claimed_count = models.PositiveIntegerField(default=0, help_text="已领取数量")
    per_user_limit = models.PositiveIntegerField(default=1, help_text="每人限领")
    required_level = models.CharField(max_length=32, blank=True, default="", help_text="所需最低会员等级，空表示不限")
    points_cost = models.PositiveIntegerField(default=0, help_text="积分兑换成本，0表示免费领取")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    valid_days = models.PositiveIntegerField(default=30, help_text="领取后有效天数")
    valid_start = models.DateField(help_text="活动开始日期")
    valid_end = models.DateField(help_text="活动结束日期")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Coupon Template"
        verbose_name_plural = "Coupon Templates"
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.name

    @property
    def remaining(self) -> int:
        return max(0, self.total_count - self.claimed_count)


class UserCoupon(models.Model):
    """用户优惠券模型。"""
    STATUS_UNUSED = "unused"
    STATUS_USED = "used"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_UNUSED, "未使用"),
        (STATUS_USED, "已使用"),
        (STATUS_EXPIRED, "已过期"),
    ]

    TYPE_CASH = "cash"
    TYPE_DISCOUNT = "discount"
    TYPE_CHOICES = [
        (TYPE_CASH, "满减券"),
        (TYPE_DISCOUNT, "折扣券"),
    ]

    user_id: int
    template_id: int | None
    used_order_id: int | None
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coupons")
    template = models.ForeignKey(CouponTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_coupons")
    name = models.CharField(max_length=100)
    coupon_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CASH)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="满减金额")
    discount = models.DecimalField(max_digits=3, decimal_places=1, default=10, help_text="折扣值")
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="最低消费门槛")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNUSED)
    used_order = models.ForeignKey("bookings.BookingOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="used_coupons")
    valid_start = models.DateField()
    valid_end = models.DateField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Coupon"
        verbose_name_plural = "User Coupons"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.user_id}-{self.name}"


class InvoiceTitle(models.Model):
    """发票抬头模型。"""
    TYPE_PERSONAL = "personal"
    TYPE_COMPANY = "company"
    TYPE_CHOICES = [
        (TYPE_PERSONAL, "个人发票"),
        (TYPE_COMPANY, "企业发票"),
    ]

    user_id: int
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoice_titles")
    invoice_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_PERSONAL)
    title = models.CharField(max_length=150)
    tax_no = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Invoice Title"
        verbose_name_plural = "Invoice Titles"
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.title


class InvoiceRequest(models.Model):
    """发票申请模型。"""
    STATUS_PENDING = "pending"
    STATUS_ISSUED = "issued"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "待处理"),
        (STATUS_ISSUED, "已开票"),
        (STATUS_CANCELLED, "已取消"),
    ]

    order_id: int
    invoice_title_id: int
    order = models.ForeignKey("bookings.BookingOrder", on_delete=models.CASCADE, related_name="invoice_requests")
    invoice_title = models.ForeignKey(InvoiceTitle, on_delete=models.CASCADE, related_name="invoice_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Invoice Request"
        verbose_name_plural = "Invoice Requests"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.order_id}-{self.invoice_title_id}"
