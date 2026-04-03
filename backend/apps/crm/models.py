from django.db import models


class CustomerProfile(models.Model):
    full_name = models.CharField(max_length=120)
    mobile = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"

    def __str__(self) -> str:
        return self.full_name
