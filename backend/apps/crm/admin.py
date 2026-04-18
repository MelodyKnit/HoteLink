"""crm admin 配置模块。"""

from django.contrib import admin
from .models import CouponTemplate, PointsLog, Review, UserCoupon


@admin.register(CouponTemplate)
class CouponTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "coupon_type", "amount", "discount", "total_count", "claimed_count", "status")
    list_filter = ("coupon_type", "status")
    search_fields = ("name",)


@admin.register(UserCoupon)
class UserCouponAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "template_id", "status", "valid_start", "valid_end", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username",)


@admin.register(PointsLog)
class PointsLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "log_type", "points", "balance", "created_at")
    list_filter = ("log_type",)
    search_fields = ("user__username", "description")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "hotel_id", "order_id", "score", "created_at")
    list_filter = ("score",)
    search_fields = ("content",)

