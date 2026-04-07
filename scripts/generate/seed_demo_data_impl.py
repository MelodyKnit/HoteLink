"""开发演示数据初始化实现（统一放在 scripts/generate）。"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
import importlib

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


def run(command, *args, **options):
    BookingOrder = importlib.import_module("apps.bookings.models").BookingOrder
    crm_models = importlib.import_module("apps.crm.models")
    InvoiceTitle = crm_models.InvoiceTitle
    Review = crm_models.Review
    UserCoupon = crm_models.UserCoupon

    hotel_models = importlib.import_module("apps.hotels.models")
    Hotel = hotel_models.Hotel
    RoomInventory = hotel_models.RoomInventory
    RoomType = hotel_models.RoomType

    SystemNotice = importlib.import_module("apps.operations.models").SystemNotice
    UserProfile = importlib.import_module("apps.users.models").UserProfile

    admin_user, _ = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"})
    admin_user.set_password("Password123")
    admin_user.is_staff = True
    admin_user.save()

    admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
    admin_profile.nickname = "系统管理员"
    admin_profile.role = UserProfile.ROLE_SYSTEM_ADMIN
    admin_profile.status = UserProfile.STATUS_ACTIVE
    admin_profile.save()

    demo_user, _ = User.objects.get_or_create(username="zhangsan", defaults={"email": "zhangsan@example.com"})
    demo_user.set_password("Password123")
    demo_user.save()

    demo_profile, _ = UserProfile.objects.get_or_create(user=demo_user)
    demo_profile.nickname = "张三"
    demo_profile.mobile = "13800138000"
    demo_profile.member_level = UserProfile.MEMBER_GOLD
    demo_profile.points = 20
    demo_profile.save()

    hotel, _ = Hotel.objects.get_or_create(
        name="HoteLink 北京国贸店",
        defaults={
            "city": "北京",
            "address": "北京市朝阳区示例路 1 号",
            "star": 4,
            "phone": "010-88886666",
            "description": "适合商务与休闲入住的现代化酒店。",
            "rating": Decimal("4.7"),
            "min_price": Decimal("399.00"),
            "is_recommended": True,
            "status": Hotel.STATUS_ONLINE,
        },
    )

    room_type, _ = RoomType.objects.get_or_create(
        hotel=hotel,
        name="豪华大床房",
        defaults={
            "bed_type": RoomType.BED_QUEEN,
            "area": 35,
            "breakfast_count": 2,
            "base_price": Decimal("399.00"),
            "max_guest_count": 2,
            "stock": 10,
            "status": RoomType.STATUS_ONLINE,
            "description": "高楼层大床房，含双早。",
        },
    )

    today = timezone.localdate()
    for offset in range(0, 7):
        RoomInventory.objects.update_or_create(
            room_type=room_type,
            date=today + timedelta(days=offset),
            defaults={
                "price": Decimal("399.00") + Decimal(offset * 10),
                "stock": 10 - offset if 10 - offset > 0 else 1,
                "status": "available",
            },
        )

    order, _ = BookingOrder.objects.get_or_create(
        order_no="HTDEMO202604040001",
        defaults={
            "user": demo_user,
            "hotel": hotel,
            "room_type": room_type,
            "status": BookingOrder.STATUS_PAID,
            "payment_status": BookingOrder.PAYMENT_PAID,
            "check_in_date": today + timedelta(days=1),
            "check_out_date": today + timedelta(days=3),
            "guest_name": "张三",
            "guest_mobile": "13800138000",
            "guest_count": 2,
            "original_amount": Decimal("798.00"),
            "discount_amount": Decimal("0.00"),
            "pay_amount": Decimal("798.00"),
        },
    )

    Review.objects.get_or_create(
        order=order,
        defaults={
            "user": demo_user,
            "hotel": hotel,
            "score": 5,
            "content": "环境很好，入住体验不错。",
            "reply_content": "感谢您的入住，欢迎再次光临。",
        },
    )

    UserCoupon.objects.get_or_create(
        user=demo_user,
        name="新客立减券",
        defaults={
            "amount": Decimal("50.00"),
            "status": UserCoupon.STATUS_UNUSED,
            "valid_start": today,
            "valid_end": today + timedelta(days=30),
        },
    )

    InvoiceTitle.objects.get_or_create(
        user=demo_user,
        title="北京测试科技有限公司",
        defaults={
            "invoice_type": InvoiceTitle.TYPE_COMPANY,
            "tax_no": "91110000123456789X",
            "email": "invoice@example.com",
        },
    )

    SystemNotice.objects.get_or_create(
        user=demo_user,
        title="欢迎使用 HoteLink",
        defaults={
            "notice_type": SystemNotice.TYPE_SYSTEM,
            "content": "演示数据已初始化，可以开始联调接口。",
        },
    )

    command.stdout.write(command.style.SUCCESS("HoteLink 演示数据初始化完成。"))
    command.stdout.write("管理员账号：admin / Password123")
    command.stdout.write("普通用户账号：zhangsan / Password123")
    return None
