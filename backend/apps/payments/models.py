"""apps/payments/models.py —— 支付记录模型。"""

from django.db import models


class PaymentRecord(models.Model):
    """订单支付流水模型。"""
    METHOD_MOCK = "mock"
    METHOD_WECHAT = "wechat"
    METHOD_ALIPAY = "alipay"
    METHOD_CASH = "cash"
    METHOD_CARD = "card"
    METHOD_CHOICES = [
        (METHOD_MOCK, "模拟支付"),
        (METHOD_WECHAT, "微信支付"),
        (METHOD_ALIPAY, "支付宝"),
        (METHOD_CASH, "现金"),
        (METHOD_CARD, "银行卡"),
    ]

    STATUS_UNPAID = "unpaid"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [
        (STATUS_UNPAID, "未支付"),
        (STATUS_PAID, "已支付"),
        (STATUS_FAILED, "支付失败"),
        (STATUS_REFUNDED, "已退款"),
    ]

    order_id: int
    order = models.ForeignKey("bookings.BookingOrder", on_delete=models.CASCADE, related_name="payments")
    payment_no = models.CharField(max_length=64, unique=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_MOCK)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNPAID)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment Record"
        verbose_name_plural = "Payment Records"
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.payment_no
