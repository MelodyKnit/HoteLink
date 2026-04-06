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
    order = models.OneToOneField("bookings.BookingOrder", on_delete=models.CASCADE, related_name="review")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="reviews")
    score = models.PositiveSmallIntegerField(default=5)
    content = models.TextField()
    reply_content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.hotel_id}-{self.score}"


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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coupons")
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNUSED)
    valid_start = models.DateField()
    valid_end = models.DateField()
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
