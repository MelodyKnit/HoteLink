"""apps/api/tests.py —— API 集成测试用例集合。"""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path
import shutil

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from apps.bookings.models import BookingOrder
from apps.crm.models import InvoiceTitle, UserCoupon
from apps.hotels.models import Hotel, RoomInventory, RoomType
from apps.users.models import UserProfile
from config.ai import _get_runtime_config_path

User = get_user_model()


class ApiBaseTestCase(APITestCase):
    """API 测试基类，准备账号、酒店、房型、订单等公共夹具。"""
    @classmethod
    def setUpTestData(cls):
        """构造全量测试基准数据。"""
        cls.admin_user = User.objects.create_user(username="admin", password="Password123")
        UserProfile.objects.create(
            user=cls.admin_user,
            nickname="管理员",
            role=UserProfile.ROLE_SYSTEM_ADMIN,
            status=UserProfile.STATUS_ACTIVE,
        )

        cls.user = User.objects.create_user(username="zhangsan", password="Password123", email="zhangsan@example.com")
        cls.profile = UserProfile.objects.create(
            user=cls.user,
            nickname="张三",
            mobile="13800138000",
            role=UserProfile.ROLE_USER,
            status=UserProfile.STATUS_ACTIVE,
            member_level=UserProfile.MEMBER_GOLD,
        )

        cls.hotel = Hotel.objects.create(
            name="HoteLink 北京国贸店",
            city="北京",
            address="北京市朝阳区示例路 1 号",
            star=4,
            phone="010-88886666",
            description="演示酒店",
            rating=Decimal("4.7"),
            min_price=Decimal("399.00"),
            is_recommended=True,
            status=Hotel.STATUS_ONLINE,
        )
        cls.room_type = RoomType.objects.create(
            hotel=cls.hotel,
            name="豪华大床房",
            bed_type=RoomType.BED_QUEEN,
            area=35,
            breakfast_count=2,
            base_price=Decimal("399.00"),
            max_guest_count=2,
            stock=10,
            status=RoomType.STATUS_ONLINE,
        )
        RoomInventory.objects.create(
            room_type=cls.room_type,
            date=timezone.localdate() + timedelta(days=1),
            price=Decimal("399.00"),
            stock=8,
            status=RoomInventory.STATUS_AVAILABLE,
        )
        cls.order = BookingOrder.objects.create(
            user=cls.user,
            hotel=cls.hotel,
            room_type=cls.room_type,
            order_no="HTTEST0001",
            status=BookingOrder.STATUS_PENDING_PAYMENT,
            payment_status=BookingOrder.PAYMENT_UNPAID,
            check_in_date=timezone.localdate() + timedelta(days=1),
            check_out_date=timezone.localdate() + timedelta(days=3),
            guest_name="张三",
            guest_mobile="13800138000",
            guest_count=2,
            original_amount=Decimal("798.00"),
            discount_amount=Decimal("0.00"),
            pay_amount=Decimal("798.00"),
        )
        UserCoupon.objects.create(
            user=cls.user,
            name="测试优惠券",
            amount=Decimal("50.00"),
            status=UserCoupon.STATUS_UNUSED,
            valid_start=timezone.localdate(),
            valid_end=timezone.localdate() + timedelta(days=30),
        )
        cls.invoice_title = InvoiceTitle.objects.create(
            user=cls.user,
            invoice_type=InvoiceTitle.TYPE_COMPANY,
            title="北京测试科技有限公司",
            tax_no="91110000123456789X",
            email="invoice@example.com",
        )

    def setUp(self):
        """清理 AI 运行时配置，避免测试间互相污染。"""
        path = _get_runtime_config_path()
        if path.exists():
            path.unlink()

    def login_user(self):
        """登录普通用户并注入 Authorization 头。"""
        response = self.client.post(
            "/api/v1/public/auth/login",
            {"username": "zhangsan", "password": "Password123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['data']['access_token']}")

    def login_admin(self):
        """登录管理员并注入 Authorization 头。"""
        response = self.client.post(
            "/api/v1/public/auth/admin-login",
            {"username": "admin", "password": "Password123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['data']['access_token']}")


class PublicApiTests(ApiBaseTestCase):
    """公共接口测试集合。"""
    def test_public_home_and_hotel_search(self):
        """验证公共首页和酒店搜索接口可用。"""
        home = self.client.get("/api/v1/public/home")
        self.assertEqual(home.status_code, 200)
        self.assertEqual(home.json()["code"], 0)

        hotels = self.client.get("/api/v1/public/hotels", {"keyword": "国贸"})
        self.assertEqual(hotels.status_code, 200)
        self.assertGreaterEqual(hotels.json()["data"]["total"], 1)

        suggest = self.client.get("/api/v1/public/hotels/search-suggest", {"keyword": "HoteLink"})
        self.assertEqual(suggest.status_code, 200)
        self.assertGreaterEqual(len(suggest.json()["data"]["items"]), 1)

    def test_common_dicts_and_cities(self):
        """验证公共字典与城市接口返回结构。"""
        cities = self.client.get("/api/v1/common/cities")
        self.assertEqual(cities.status_code, 200)
        self.assertEqual(cities.json()["data"]["items"][0]["value"], "北京")

        dicts_response = self.client.get("/api/v1/common/dicts", {"types": "hotel_star,payment_method"})
        self.assertEqual(dicts_response.status_code, 200)
        self.assertIn("hotel_star", dicts_response.json()["data"])
        self.assertIn("payment_method", dicts_response.json()["data"])


class UserApiTests(ApiBaseTestCase):
    """用户端接口测试集合。"""
    def test_user_order_flow(self):
        """验证用户创建订单并支付的核心流程。"""
        self.login_user()

        create_response = self.client.post(
            "/api/v1/user/orders/create",
            {
                "hotel_id": self.hotel.id,
                "room_type_id": self.room_type.id,
                "check_in_date": str(timezone.localdate() + timedelta(days=2)),
                "check_out_date": str(timezone.localdate() + timedelta(days=4)),
                "guest_name": "李四",
                "guest_mobile": "13900139000",
                "guest_count": 2,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 200)
        order_id = create_response.json()["data"]["order_id"]

        pay_response = self.client.post(
            "/api/v1/user/orders/pay",
            {"order_id": order_id, "payment_method": "mock"},
            format="json",
        )
        self.assertEqual(pay_response.status_code, 200)
        self.assertEqual(pay_response.json()["data"]["payment_status"], "paid")

    def test_user_profile_upload_password_coupon_and_invoice(self):
        """验证头像上传、改密、优惠券和开票流程。"""
        self.login_user()
        test_media_root = Path(__file__).resolve().parents[3] / "test_media"
        if test_media_root.exists():
            shutil.rmtree(test_media_root)
        with override_settings(MEDIA_ROOT=test_media_root):
            upload_response = self.client.post(
                "/api/v1/user/profile/avatar",
                {"avatar": SimpleUploadedFile("avatar.txt", b"avatar-content", content_type="text/plain")},
                format="multipart",
            )
        if test_media_root.exists():
            shutil.rmtree(test_media_root)
        self.assertEqual(upload_response.status_code, 200)
        self.assertIn("/media/avatars/", upload_response.json()["data"]["avatar"])

        password_response = self.client.post(
            "/api/v1/user/profile/change-password",
            {
                "old_password": "Password123",
                "new_password": "Password456",
                "confirm_password": "Password456",
            },
            format="json",
        )
        self.assertEqual(password_response.status_code, 200)

        coupons_response = self.client.get("/api/v1/user/coupons")
        self.assertEqual(coupons_response.status_code, 200)
        self.assertGreaterEqual(coupons_response.json()["data"]["total"], 1)

        invoice_apply = self.client.post(
            "/api/v1/user/invoices/apply",
            {"order_id": self.order.id, "invoice_title_id": self.invoice_title.id},
            format="json",
        )
        self.assertEqual(invoice_apply.status_code, 200)
        self.assertEqual(invoice_apply.json()["data"]["status"], "pending")

    def test_user_ai_chat_returns_booking_assistant_options(self):
        """验证 AI 订房可返回结构化城市与房型动作。"""
        self.login_user()
        shanghai_hotel = Hotel.objects.create(
            name="HoteLink 上海外滩店",
            city="上海",
            address="上海市黄浦区示例路 8 号",
            star=5,
            phone="021-66668888",
            description="外滩景观酒店",
            rating=Decimal("4.9"),
            min_price=Decimal("899.00"),
            is_recommended=True,
            status=Hotel.STATUS_ONLINE,
        )
        shanghai_room = RoomType.objects.create(
            hotel=shanghai_hotel,
            name="江景大床房",
            bed_type=RoomType.BED_QUEEN,
            area=42,
            breakfast_count=2,
            base_price=Decimal("899.00"),
            max_guest_count=2,
            stock=6,
            status=RoomType.STATUS_ONLINE,
        )

        city_response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "general",
                "question": "我想订酒店",
            },
            format="json",
        )
        self.assertEqual(city_response.status_code, 200)
        city_data = city_response.json()["data"]
        self.assertEqual(city_data["booking_assistant"]["phase"], "select_city")
        self.assertTrue(any(item["label"] == "北京" for item in city_data["booking_assistant"]["options"]))

        room_response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "general",
                "question": "我想订 HoteLink 上海外滩店",
            },
            format="json",
        )
        self.assertEqual(room_response.status_code, 200)
        room_data = room_response.json()["data"]
        self.assertEqual(room_data["booking_assistant"]["phase"], "select_room_type")
        option = room_data["booking_assistant"]["options"][0]
        self.assertEqual(option["type"], "navigate_booking")
        self.assertEqual(option["label"], shanghai_room.name)
        self.assertEqual(option["query"]["hotel_id"], str(shanghai_hotel.id))
        self.assertEqual(option["query"]["room_type_id"], str(shanghai_room.id))

    def test_user_ai_chat_stream_returns_booking_meta_events(self):
        """验证 AI 订房流式接口会先返回结构化 meta 事件。"""
        self.login_user()

        response = self.client.post(
            "/api/v1/user/ai/chat/stream",
            {
                "scene": "general",
                "question": "我想订酒店",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn('"type": "meta"', payload)
        self.assertIn('"phase": "select_city"', payload)
        self.assertIn('"type": "chunk"', payload)
        self.assertIn('"type": "done"', payload)


class AdminApiTests(ApiBaseTestCase):
    """管理端接口测试集合。"""
    def test_admin_dashboard_inventory_and_settings(self):
        """验证管理端总览、库存更新和设置接口。"""
        self.login_admin()

        overview = self.client.get("/api/v1/admin/dashboard/overview")
        self.assertEqual(overview.status_code, 200)
        self.assertEqual(overview.json()["code"], 0)

        inventory = self.client.post(
            "/api/v1/admin/inventory/update",
            {
                "room_type_id": self.room_type.id,
                "date": str(timezone.localdate() + timedelta(days=5)),
                "price": "499.00",
                "stock": 6,
                "status": "available",
            },
            format="json",
        )
        self.assertEqual(inventory.status_code, 200)
        self.assertEqual(inventory.json()["data"]["stock"], 6)

        settings_response = self.client.get("/api/v1/admin/settings")
        self.assertEqual(settings_response.status_code, 200)
        self.assertEqual(settings_response.json()["data"]["platform_name"], "HoteLink 酒店管理系统")

        ai_settings = self.client.get("/api/v1/admin/ai/settings")
        self.assertEqual(ai_settings.status_code, 200)
        self.assertIn("active_provider", ai_settings.json()["data"])

    def test_admin_can_create_employee(self):
        """验证管理员创建员工账号流程。"""
        self.login_admin()
        response = self.client.post(
            "/api/v1/admin/employees/create",
            {
                "username": "frontdesk01",
                "password": "Password123",
                "name": "前台小王",
                "mobile": "13800138001",
                "role": "hotel_admin",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["role"], "hotel_admin")

    def test_admin_ai_provider_crud_and_switch(self):
        """验证 AI 供应商新增、切换、读取流程。"""
        self.login_admin()

        add_response = self.client.post(
            "/api/v1/admin/ai/provider/add",
            {
                "name": "testprovider",
                "label": "Test Provider",
                "base_url": "https://example.com/v1",
                "api_key": "test-key",
                "chat_model": "test-chat-model",
                "reasoning_model": "test-reasoning-model",
            },
            format="json",
        )
        self.assertEqual(add_response.status_code, 200)
        self.assertEqual(add_response.json()["code"], 0)

        switch_response = self.client.post(
            "/api/v1/admin/ai/provider/switch",
            {"provider_name": "testprovider"},
            format="json",
        )
        self.assertEqual(switch_response.status_code, 200)
        self.assertEqual(switch_response.json()["data"]["active_provider"], "testprovider")

        settings_response = self.client.get("/api/v1/admin/ai/settings")
        self.assertEqual(settings_response.status_code, 200)
        providers = settings_response.json()["data"]["providers"]
        self.assertTrue(any(item["name"] == "testprovider" for item in providers))

    def test_admin_system_reset_requires_confirmation(self):
        """验证系统重置接口必须输入 RESET 确认。"""
        self.login_admin()
        response = self.client.post(
            "/api/v1/admin/system/reset",
            {"confirm": "WRONG"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(response.json()["code"], 0)

    def test_admin_system_reset_success(self):
        """验证系统重置成功执行并返回删除统计。"""
        self.login_admin()
        response = self.client.post(
            "/api/v1/admin/system/reset",
            {"confirm": "RESET"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["code"], 0)
        self.assertTrue(response.json()["data"]["reset"])
        self.assertIn("deleted_counts", response.json()["data"])
