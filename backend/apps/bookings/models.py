"""apps/bookings/models.py —— 订单核心数据模型。"""

from django.conf import settings
from django.db import models


class BookingOrder(models.Model):
    """用户预订订单模型，记录支付状态与入住周期。"""
    STATUS_PENDING_PAYMENT = "pending_payment"
    STATUS_PAID = "paid"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CHECKED_IN = "checked_in"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUNDING = "refunding"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, "待支付"),
        (STATUS_PAID, "已支付"),
        (STATUS_CONFIRMED, "已确认"),
        (STATUS_CHECKED_IN, "已入住"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_CANCELLED, "已取消"),
        (STATUS_REFUNDING, "退款中"),
        (STATUS_REFUNDED, "已退款"),
    ]

    PAYMENT_UNPAID = "unpaid"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"
    PAYMENT_REFUNDED = "refunded"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID, "未支付"),
        (PAYMENT_PAID, "已支付"),
        (PAYMENT_FAILED, "支付失败"),
        (PAYMENT_REFUNDED, "已退款"),
    ]

    user_id: int
    hotel_id: int
    room_type_id: int
    coupon_id: int | None
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_orders")
    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.PROTECT, related_name="booking_orders")
    room_type = models.ForeignKey("hotels.RoomType", on_delete=models.PROTECT, related_name="booking_orders")
    order_no = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING_PAYMENT)
    payment_status = models.CharField(max_length=32, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_UNPAID)
    paid_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    guest_name = models.CharField(max_length=100)
    guest_mobile = models.CharField(max_length=20)
    guest_count = models.PositiveIntegerField(default=1)
    room_no = models.CharField(max_length=20, blank=True)
    remark = models.CharField(max_length=255, blank=True)
    operator_remark = models.CharField(max_length=255, blank=True)
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    member_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="会员折扣减免")
    coupon_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="优惠券减免")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pay_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.ForeignKey("crm.UserCoupon", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    points_earned = models.PositiveIntegerField(default=0, help_text="本单获得积分")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Booking Order"
        verbose_name_plural = "Booking Orders"
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.order_no
