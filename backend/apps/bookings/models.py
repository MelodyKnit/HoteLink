from django.db import models


class BookingOrder(models.Model):
    order_no = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=32, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Booking Order"
        verbose_name_plural = "Booking Orders"

    def __str__(self) -> str:
        return self.order_no
