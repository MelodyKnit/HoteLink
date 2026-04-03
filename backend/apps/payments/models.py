from django.db import models


class PaymentRecord(models.Model):
    payment_no = models.CharField(max_length=64, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment Record"
        verbose_name_plural = "Payment Records"

    def __str__(self) -> str:
        return self.payment_no
