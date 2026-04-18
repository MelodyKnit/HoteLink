"""apps/api/tests.py —— API 集成测试用例集合。"""

from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import shutil
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from apps.bookings.models import BookingOrder
from apps.bookings.tasks import sweep_order_lifecycle_anomalies
from apps.crm.models import ChatMessage, ChatSession, InvoiceTitle, Review, UserCoupon
from apps.hotels.models import Hotel, RoomInventory, RoomType
from apps.operations.models import AICallLog, SystemNotice
from apps.payments.models import PaymentRecord
from apps.users.models import UserProfile
from config.ai import _get_runtime_config_path
from PIL import Image

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
        cls.hotel_admin_user = User.objects.create_user(username="hoteladmin", password="Password123")
        UserProfile.objects.create(
            user=cls.hotel_admin_user,
            nickname="店长",
            mobile="13800138002",
            role=UserProfile.ROLE_HOTEL_ADMIN,
            status=UserProfile.STATUS_ACTIVE,
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
        for extra_day in range(2, 5):
            RoomInventory.objects.create(
                room_type=cls.room_type,
                date=timezone.localdate() + timedelta(days=extra_day),
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
        cache.clear()
        path = _get_runtime_config_path()
        if path.exists():
            path.unlink()
        try:
            from apps.operations.models import RuntimeConfig

            RuntimeConfig.objects.filter(key="ai_runtime").delete()
        except Exception:
            pass

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

    def login_hotel_admin(self):
        """登录酒店管理员并注入 Authorization 头。"""
        response = self.client.post(
            "/api/v1/public/auth/admin-login",
            {"username": "hoteladmin", "password": "Password123"},
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

    def test_user_pay_timeout_order_should_auto_cancel(self):
        """验证支付超时订单时会被自动取消，避免长期挂起。"""
        self.login_user()
        stale_created_at = timezone.now() - timedelta(minutes=45)
        BookingOrder.objects.filter(id=self.order.id).update(created_at=stale_created_at)

        pay_response = self.client.post(
            "/api/v1/user/orders/pay",
            {"order_id": self.order.id, "payment_method": "mock"},
            format="json",
        )
        self.assertEqual(pay_response.status_code, 409)
        self.assertEqual(pay_response.json()["code"], 4093)
        self.assertIn("超时", pay_response.json()["message"])

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, BookingOrder.STATUS_CANCELLED)
        self.assertEqual(self.order.payment_status, BookingOrder.PAYMENT_UNPAID)
        self.assertIn("超过", self.order.operator_remark)

    def test_user_profile_upload_password_coupon_and_invoice(self):
        """验证头像上传、改密、优惠券和开票流程。"""
        self.login_user()
        test_media_root = Path(__file__).resolve().parents[3] / "test_media"
        if test_media_root.exists():
            shutil.rmtree(test_media_root)
        avatar_buffer = BytesIO()
        Image.new("RGB", (2, 2), color=(240, 240, 240)).save(avatar_buffer, format="PNG")
        with override_settings(MEDIA_ROOT=test_media_root):
            upload_response = self.client.post(
                "/api/v1/user/profile/avatar",
                {
                    "avatar": SimpleUploadedFile(
                        "avatar.png",
                        avatar_buffer.getvalue(),
                        content_type="image/png",
                    )
                },
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
                "new_password": "HoteLink#Password456",
                "confirm_password": "HoteLink#Password456",
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

    def test_user_notices_should_include_related_order_fields(self):
        """验证通知列表会返回订单关联字段，支持前端直达订单详情。"""
        self.login_user()
        SystemNotice.objects.create(
            user=self.user,
            notice_type=SystemNotice.TYPE_ORDER,
            title="订单状态更新",
            content=f"订单 {self.order.order_no} 已更新。",
            related_order=self.order,
        )

        response = self.client.get("/api/v1/user/notices")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertGreaterEqual(payload["total"], 1)

        target = next(
            (item for item in payload["items"] if item["title"] == "订单状态更新"),
            None,
        )
        self.assertIsNotNone(target)
        self.assertEqual(target["related_order_id"], self.order.id)
        self.assertEqual(target["related_order_no"], self.order.order_no)

    def test_user_orders_list_should_support_keyword_and_advanced_filters(self):
        """验证用户订单列表支持关键词与多条件组合筛选。"""
        self.login_user()
        second_hotel = Hotel.objects.create(
            name="HoteLink 上海陆家嘴店",
            city="上海",
            address="上海市浦东新区示例路 99 号",
            star=5,
            phone="021-77778888",
            description="测试酒店",
            rating=Decimal("4.8"),
            min_price=Decimal("699.00"),
            is_recommended=True,
            status=Hotel.STATUS_ONLINE,
        )
        second_room_type = RoomType.objects.create(
            hotel=second_hotel,
            name="行政套房",
            bed_type=RoomType.BED_QUEEN,
            area=55,
            breakfast_count=2,
            base_price=Decimal("1288.00"),
            max_guest_count=2,
            stock=6,
            status=RoomType.STATUS_ONLINE,
        )
        target_order = BookingOrder.objects.create(
            user=self.user,
            hotel=second_hotel,
            room_type=second_room_type,
            order_no="HTSEARCH0002",
            status=BookingOrder.STATUS_CONFIRMED,
            payment_status=BookingOrder.PAYMENT_PAID,
            check_in_date=timezone.localdate() + timedelta(days=10),
            check_out_date=timezone.localdate() + timedelta(days=12),
            guest_name="王五",
            guest_mobile="13700137000",
            guest_count=1,
            original_amount=Decimal("1288.00"),
            discount_amount=Decimal("0.00"),
            pay_amount=Decimal("1288.00"),
        )
        BookingOrder.objects.filter(id=target_order.id).update(created_at=timezone.now() - timedelta(days=2))

        other_user = User.objects.create_user(username="lisi", password="Password123")
        BookingOrder.objects.create(
            user=other_user,
            hotel=second_hotel,
            room_type=second_room_type,
            order_no="HTSEARCH0003",
            status=BookingOrder.STATUS_CONFIRMED,
            payment_status=BookingOrder.PAYMENT_PAID,
            check_in_date=timezone.localdate() + timedelta(days=10),
            check_out_date=timezone.localdate() + timedelta(days=12),
            guest_name="王五",
            guest_mobile="13600136000",
            guest_count=1,
            original_amount=Decimal("1288.00"),
            discount_amount=Decimal("0.00"),
            pay_amount=Decimal("1288.00"),
        )

        keyword_response = self.client.get("/api/v1/user/orders", {"keyword": "王五"})
        self.assertEqual(keyword_response.status_code, 200)
        keyword_payload = keyword_response.json()["data"]
        self.assertEqual(keyword_payload["total"], 1)
        self.assertEqual(keyword_payload["items"][0]["id"], target_order.id)

        advanced_response = self.client.get(
            "/api/v1/user/orders",
            {
                "status": BookingOrder.STATUS_CONFIRMED,
                "payment_status": BookingOrder.PAYMENT_PAID,
                "keyword": "陆家嘴",
                "check_in_start": str(timezone.localdate() + timedelta(days=9)),
                "check_in_end": str(timezone.localdate() + timedelta(days=11)),
                "created_start": str(timezone.localdate() - timedelta(days=5)),
                "created_end": str(timezone.localdate() - timedelta(days=1)),
                "amount_min": "1000",
                "amount_max": "1300",
            },
        )
        self.assertEqual(advanced_response.status_code, 200)
        advanced_payload = advanced_response.json()["data"]
        self.assertEqual(advanced_payload["total"], 1)
        self.assertEqual(advanced_payload["items"][0]["id"], target_order.id)

    def test_user_orders_list_should_return_400_for_invalid_ranges(self):
        """验证用户订单列表在日期/金额区间非法时返回参数错误。"""
        self.login_user()
        response = self.client.get(
            "/api/v1/user/orders",
            {
                "created_start": "2026-05-20",
                "created_end": "2026-05-01",
                "amount_min": "100",
                "amount_max": "50",
            },
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["code"], 4001)
        self.assertIn("created_range", payload["data"]["errors"])
        self.assertIn("amount_range", payload["data"]["errors"])

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

    def test_user_ai_chat_customer_service_should_not_trigger_booking_assistant(self):
        """验证客服场景咨询订单操作时，不会误触发订房助手流程。"""
        self.login_user()
        response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "customer_service",
                "question": "我想取消订单，应该怎么操作？",
                "order_id": self.order.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["scene"], "customer_service")
        self.assertIsNotNone(data.get("booking_assistant"))
        self.assertTrue(data["booking_assistant"]["options"])
        self.assertTrue(any(option["route"] == f"/my/orders/{self.order.id}" for option in data["booking_assistant"]["options"]))

    def test_user_ai_chat_customer_service_should_not_call_booking_builder(self):
        """验证 customer_service 场景不会调用订房助手构建逻辑。"""
        self.login_user()
        with patch(
            "apps.operations.services.ai_service.AIChatService._build_booking_assistant_response",
            side_effect=AssertionError("customer_service should not invoke booking flow"),
        ):
            response = self.client.post(
                "/api/v1/user/ai/chat",
                {
                    "scene": "customer_service",
                    "question": "我的订单现在什么状态？",
                    "order_id": self.order.id,
                },
                format="json",
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["scene"], "customer_service")
        self.assertIsNotNone(data.get("booking_assistant"))

    def test_user_ai_chat_general_customer_question_should_route_to_customer_service(self):
        """验证 general 场景下客服类问题会路由到客服模式。"""
        self.login_user()
        response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "general",
                "question": "怎么取消我的订单？",
                "order_id": self.order.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["scene"], "customer_service")
        self.assertIsNotNone(data.get("booking_assistant"))
        self.assertTrue(data["booking_assistant"]["options"])

    def test_user_ai_chat_customer_service_actions_should_include_protocol_fields(self):
        """验证客服快捷操作包含统一动作协议字段。"""
        self.login_user()
        response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "customer_service",
                "question": "帮我取消订单",
                "order_id": self.order.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        action_payload = data["booking_assistant"]
        self.assertEqual(action_payload["phase"], "quick_actions")
        self.assertEqual(action_payload["context"]["detected_intent"], "cancel_order")

        cancel_option = next(
            (option for option in action_payload["options"] if option["type"] == "navigate_cancel_order"),
            None,
        )
        self.assertIsNotNone(cancel_option)
        self.assertEqual(cancel_option["action_type"], "navigate")
        self.assertTrue(cancel_option["requires_confirmation"])
        self.assertEqual(cancel_option["target"], f"/my/orders/{self.order.id}")
        self.assertEqual(cancel_option["query"]["source"], "ai")
        self.assertIn("tracking_id", cancel_option)

    def test_user_ai_chat_customer_service_should_offer_booking_switch_action(self):
        """验证客服场景遇到订房诉求时，会给出切换到订房助手的快捷入口。"""
        self.login_user()
        question = "我想订酒店，帮我推荐一下"
        response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "customer_service",
                "question": question,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["scene"], "customer_service")
        options = data["booking_assistant"]["options"]
        switch_option = next(
            (option for option in options if option["type"] == "navigate_ai_booking" and option["route"] == "/ai-booking"),
            None,
        )
        self.assertIsNotNone(switch_option)
        self.assertEqual(switch_option["query"]["source"], "ai")
        self.assertEqual(switch_option["query"]["from"], "ai-chat")
        self.assertEqual(switch_option["query"]["ask"], question)

    def test_user_ai_chat_customer_service_should_offer_review_action(self):
        """验证客服识别评价问题并提供“我的评价”快捷入口。"""
        self.login_user()
        completed_order = BookingOrder.objects.create(
            user=self.user,
            hotel=self.hotel,
            room_type=self.room_type,
            order_no="HTTEST0002",
            status=BookingOrder.STATUS_COMPLETED,
            payment_status=BookingOrder.PAYMENT_PAID,
            check_in_date=timezone.localdate() - timedelta(days=3),
            check_out_date=timezone.localdate() - timedelta(days=1),
            guest_name="张三",
            guest_mobile="13800138000",
            guest_count=2,
            original_amount=Decimal("798.00"),
            discount_amount=Decimal("0.00"),
            pay_amount=Decimal("798.00"),
        )
        Review.objects.create(
            user=self.user,
            order=completed_order,
            hotel=self.hotel,
            score=5,
            content="服务很好，房间整洁。",
        )

        response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "customer_service",
                "question": "我有哪些评价？",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        options = data["booking_assistant"]["options"]
        review_option = next((option for option in options if option["type"] == "navigate_reviews"), None)
        self.assertIsNotNone(review_option)
        self.assertEqual(review_option["route"], "/my/reviews")

    def test_user_ai_chat_booking_assistant_scene_should_return_booking_scene(self):
        """验证 booking_assistant 场景会返回 booking_assistant scene。"""
        self.login_user()
        response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "booking_assistant",
                "question": "我想订酒店",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["scene"], "booking_assistant")
        self.assertIsNotNone(data.get("booking_assistant"))

    def test_user_ai_chat_booking_assistant_should_offer_customer_service_switch_action(self):
        """验证订房场景遇到客服诉求时，会给出切换到客服助手的快捷入口。"""
        self.login_user()
        question = "帮我取消订单并退款"
        response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "booking_assistant",
                "question": question,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["scene"], "booking_assistant")

        assistant_payload = data["booking_assistant"]
        self.assertEqual(assistant_payload["phase"], "switch_to_customer_service")
        switch_option = next(
            (
                option
                for option in assistant_payload["options"]
                if option["type"] == "navigate_ai_customer_service" and option["route"] == "/ai-chat"
            ),
            None,
        )
        self.assertIsNotNone(switch_option)
        self.assertEqual(switch_option["action_type"], "navigate")
        self.assertEqual(switch_option["query"]["source"], "ai")
        self.assertEqual(switch_option["query"]["from"], "ai-booking")
        self.assertEqual(switch_option["query"]["ask"], question)

    def test_user_ai_chat_stream_customer_service_should_not_return_booking_meta(self):
        """验证客服场景流式接口会返回客服快捷动作 meta 数据。"""
        self.login_user()
        response = self.client.post(
            "/api/v1/user/ai/chat/stream",
            {
                "scene": "customer_service",
                "question": "怎么取消我这个订单？",
                "order_id": self.order.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn('"type": "meta"', payload)
        self.assertIn('"scene": "customer_service"', payload)
        self.assertIn('"booking_assistant"', payload)
        self.assertIn('"phase": "quick_actions"', payload)

    def test_user_ai_chat_should_persist_session_and_messages(self):
        """验证 AI 对话会自动落库会话与消息。"""
        self.login_user()
        with patch(
            "apps.api.views.AIChatService.reply_customer_service",
            return_value={
                "scene": "customer_service",
                "answer": "这是测试回复",
                "booking_assistant": None,
            },
        ):
            response = self.client.post(
                "/api/v1/user/ai/chat",
                {"scene": "general", "question": "你好"},
                format="json",
            )
        self.assertEqual(response.status_code, 200)
        session_id = response.json()["data"].get("session_id")
        self.assertTrue(session_id)

        session = ChatSession.objects.filter(id=session_id, user=self.user).first()
        self.assertIsNotNone(session)
        self.assertEqual(session.message_count, 2)

        messages = list(ChatMessage.objects.filter(session_id=session_id).order_by("id"))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, ChatMessage.ROLE_USER)
        self.assertEqual(messages[0].content, "你好")
        self.assertEqual(messages[1].role, ChatMessage.ROLE_ASSISTANT)
        self.assertEqual(messages[1].content, "这是测试回复")

    def test_user_ai_chat_stream_should_not_invoke_second_llm_call(self):
        """验证流式接口不会在同一轮对话重复调用模型。"""
        self.login_user()
        with patch(
            "apps.api.views.AIChatService.reply_customer_service",
            return_value={
                "scene": "customer_service",
                "answer": "流式测试回复",
                "booking_assistant": None,
            },
        ), patch("apps.api.views.AIChatService.stream_chat_completion") as mocked_stream:
            response = self.client.post(
                "/api/v1/user/ai/chat/stream",
                {"scene": "general", "question": "帮我查订单"},
                format="json",
            )
        self.assertEqual(response.status_code, 200)
        payload = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn('"type": "meta"', payload)
        self.assertIn('"type": "chunk"', payload)
        self.assertFalse(mocked_stream.called)

    def test_user_ai_chat_switch_city_overrides_previous_context(self):
        """验证用户改选城市时，订房助手会覆盖历史上下文并返回新城市酒店。"""
        self.login_user()
        shanghai_hotel = Hotel.objects.create(
            name="HoteLink 上海陆家嘴店",
            city="上海",
            address="上海市浦东新区示例路 9 号",
            star=5,
            phone="021-66669999",
            description="陆家嘴商务酒店",
            rating=Decimal("4.8"),
            min_price=Decimal("899.00"),
            is_recommended=True,
            status=Hotel.STATUS_ONLINE,
        )

        response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "general",
                "question": "还是选北京吧",
                "booking_context": {
                    "intent": "hotel_booking",
                    "selected_city": "上海",
                    "selected_hotel_id": shanghai_hotel.id,
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]["booking_assistant"]
        self.assertEqual(data["phase"], "select_hotel")
        self.assertEqual(data["context"]["selected_city"], "北京")
        self.assertIsNone(data["context"]["selected_hotel_id"])
        self.assertTrue(any(option["label"] == self.hotel.name for option in data["options"]))

    def test_user_ai_chat_hotel_keyword_should_not_fallback_to_city_selection(self):
        """验证用户明确说出酒店关键词时，订房助手应直接进入酒店/房型选择。"""
        self.login_user()
        target_hotel = Hotel.objects.create(
            name="HoteLink 深圳湾景店",
            city="深圳",
            address="深圳市南山区示例路 21 号",
            star=5,
            phone="0755-66668888",
            description="湾景商务酒店",
            rating=Decimal("4.8"),
            min_price=Decimal("799.00"),
            is_recommended=True,
            status=Hotel.STATUS_ONLINE,
        )
        RoomType.objects.create(
            hotel=target_hotel,
            name="湾景大床房",
            bed_type=RoomType.BED_QUEEN,
            area=38,
            breakfast_count=2,
            base_price=Decimal("799.00"),
            max_guest_count=2,
            stock=6,
            status=RoomType.STATUS_ONLINE,
        )

        response = self.client.post(
            "/api/v1/user/ai/chat",
            {
                "scene": "general",
                "question": "我想订深圳湾景店",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]["booking_assistant"]
        self.assertIn(data["phase"], ["select_hotel", "select_room_type"])
        self.assertEqual(data["context"]["selected_city"], "深圳")
        if data["phase"] == "select_hotel":
            self.assertTrue(any(option["label"] == target_hotel.name for option in data["options"]))

    def test_user_ai_hotel_compare_should_use_online_hotels_and_return_fallback_payload(self):
        """验证酒店对比接口可识别上架酒店，并在 AI 不可用时返回稳定兜底结构。"""
        self.login_user()
        second_hotel = Hotel.objects.create(
            name="HoteLink 广州天河店",
            city="广州",
            address="广州市天河区示例路 18 号",
            star=4,
            phone="020-12345678",
            description="广州示例酒店",
            rating=Decimal("4.6"),
            min_price=Decimal("499.00"),
            is_recommended=True,
            status=Hotel.STATUS_ONLINE,
        )
        RoomType.objects.create(
            hotel=second_hotel,
            name="行政大床房",
            bed_type=RoomType.BED_QUEEN,
            area=38,
            breakfast_count=2,
            base_price=Decimal("499.00"),
            max_guest_count=2,
            stock=5,
            status=RoomType.STATUS_ONLINE,
        )

        with patch("apps.api.views.AIChatService.is_available", return_value=False):
            response = self.client.post(
                "/api/v1/user/ai/hotel-compare",
                {
                    "hotel_ids": [self.hotel.id, second_hotel.id],
                    "check_in_date": str(timezone.localdate() + timedelta(days=1)),
                    "check_out_date": str(timezone.localdate() + timedelta(days=2)),
                },
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertEqual(payload["data"]["scene"], "hotel_compare")
        self.assertEqual(len(payload["data"]["hotels"]), 2)
        self.assertIn("recommendation", payload["data"])
        self.assertIn("ai_generated", payload["data"])
        self.assertFalse(payload["data"]["ai_generated"])

    def test_user_ai_hotel_compare_should_reject_invalid_date_range(self):
        """验证酒店对比接口会拦截退房日期早于或等于入住日期的请求。"""
        self.login_user()
        second_hotel = Hotel.objects.create(
            name="HoteLink 杭州西湖店",
            city="杭州",
            address="杭州市西湖区示例路 6 号",
            star=5,
            phone="0571-12345678",
            description="杭州示例酒店",
            rating=Decimal("4.8"),
            min_price=Decimal("699.00"),
            is_recommended=True,
            status=Hotel.STATUS_ONLINE,
        )

        response = self.client.post(
            "/api/v1/user/ai/hotel-compare",
            {
                "hotel_ids": [self.hotel.id, second_hotel.id],
                "check_in_date": "2026-05-20",
                "check_out_date": "2026-05-20",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["code"], 4001)
        self.assertIn("check_out_date", payload["data"]["errors"])

    def test_user_ai_hotel_compare_should_reject_duplicate_hotel_ids(self):
        """验证酒店对比接口会拒绝重复酒店 ID，避免无效对比。"""
        self.login_user()
        response = self.client.post(
            "/api/v1/user/ai/hotel-compare",
            {"hotel_ids": [self.hotel.id, self.hotel.id]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["code"], 4001)
        self.assertIn("hotel_ids", payload["data"]["errors"])


class AdminApiTests(ApiBaseTestCase):
    """管理端接口测试集合。"""
    def test_admin_hotels_list_should_support_query_filters(self):
        """验证管理端酒店列表可正常返回并支持筛选参数。"""
        self.login_admin()
        response = self.client.get(
            "/api/v1/admin/hotels",
            {
                "keyword": "国贸",
                "status": Hotel.STATUS_ONLINE,
                "type": Hotel.TYPE_HOTEL,
                "ordering": "-id",
                "w": 80,
                "h": 60,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertGreaterEqual(payload["total"], 1)
        self.assertTrue(any(item["id"] == self.hotel.id for item in payload["items"]))

    def test_admin_order_detail_should_include_payments_and_status_timestamps(self):
        """验证管理端订单详情返回支付记录与关键状态时间字段。"""
        self.login_admin()
        paid_at = timezone.now()
        BookingOrder.objects.filter(id=self.order.id).update(
            status=BookingOrder.STATUS_PAID,
            payment_status=BookingOrder.PAYMENT_PAID,
            paid_at=paid_at,
        )
        PaymentRecord.objects.create(
            order_id=self.order.id,
            payment_no="PMTEST0001",
            method="mock",
            status=PaymentRecord.STATUS_PAID,
            amount=Decimal("798.00"),
            paid_at=paid_at,
        )

        response = self.client.get("/api/v1/admin/orders/detail", {"order_id": self.order.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn("payments", data)
        self.assertEqual(len(data["payments"]), 1)
        self.assertEqual(data["payments"][0]["payment_no"], "PMTEST0001")
        self.assertTrue(data.get("paid_at"))

    def test_lifecycle_sweep_should_auto_complete_overdue_checked_in_order(self):
        """验证生命周期巡检会自动完结离店日已过的在住订单。"""
        today = timezone.localdate()
        BookingOrder.objects.filter(id=self.order.id).update(
            status=BookingOrder.STATUS_CHECKED_IN,
            payment_status=BookingOrder.PAYMENT_PAID,
            check_in_date=today - timedelta(days=3),
            check_out_date=today - timedelta(days=1),
            operator_remark="",
        )

        sweep_order_lifecycle_anomalies.run(batch_size=20)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, BookingOrder.STATUS_COMPLETED)
        self.assertIn("系统自动完结", self.order.operator_remark)

    def test_lifecycle_sweep_should_mark_overdue_paid_order_as_anomaly(self):
        """验证生命周期巡检会标记过期未入住的已支付订单。"""
        today = timezone.localdate()
        BookingOrder.objects.filter(id=self.order.id).update(
            status=BookingOrder.STATUS_PAID,
            payment_status=BookingOrder.PAYMENT_PAID,
            check_in_date=today - timedelta(days=3),
            check_out_date=today - timedelta(days=1),
            operator_remark="",
        )

        sweep_order_lifecycle_anomalies.run(batch_size=20)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, BookingOrder.STATUS_PAID)
        self.assertIn("异常提醒", self.order.operator_remark)

    def test_admin_check_in_should_reject_overdue_checkout_order(self):
        """验证离店日已过的订单不可再办理入住。"""
        self.login_admin()
        today = timezone.localdate()
        BookingOrder.objects.filter(id=self.order.id).update(
            status=BookingOrder.STATUS_PAID,
            payment_status=BookingOrder.PAYMENT_PAID,
            check_in_date=today - timedelta(days=3),
            check_out_date=today - timedelta(days=1),
        )

        response = self.client.post(
            "/api/v1/admin/orders/check-in",
            {"order_id": self.order.id, "room_no": "1808"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("超过离店日期", response.json()["message"])

    def test_admin_order_list_should_return_lifecycle_warning(self):
        """验证管理端订单列表返回生命周期异常提示字段。"""
        self.login_admin()
        today = timezone.localdate()
        BookingOrder.objects.filter(id=self.order.id).update(
            status=BookingOrder.STATUS_PAID,
            payment_status=BookingOrder.PAYMENT_PAID,
            check_in_date=today - timedelta(days=3),
            check_out_date=today - timedelta(days=1),
            operator_remark="",
        )

        response = self.client.get("/api/v1/admin/orders", {"status": BookingOrder.STATUS_PAID})
        self.assertEqual(response.status_code, 200)
        item = response.json()["data"]["items"][0]
        self.assertTrue(item["is_lifecycle_anomaly"])
        self.assertIn("离店日", item["lifecycle_warning"])

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
        self.assertIn("support_email", settings_response.json()["data"])

        ai_settings = self.client.get("/api/v1/admin/ai/settings")
        self.assertEqual(ai_settings.status_code, 200)
        self.assertIn("active_provider", ai_settings.json()["data"])

    def test_admin_hotel_and_room_create_should_reject_duplicates(self):
        """验证酒店与房型重复创建会返回明确错误。"""
        self.login_admin()

        duplicate_hotel_response = self.client.post(
            "/api/v1/admin/hotels/create",
            {
                "name": self.hotel.name,
                "city": "北京",
                "address": "北京市朝阳区重复路 2 号",
                "star": 4,
                "phone": "010-77778888",
                "description": "重复酒店测试",
                "rating": "4.6",
                "min_price": "488.00",
                "status": "online",
            },
            format="json",
        )
        self.assertEqual(duplicate_hotel_response.status_code, 409)
        self.assertEqual(duplicate_hotel_response.json()["code"], 4090)
        self.assertIn("name", duplicate_hotel_response.json()["data"]["errors"])

        duplicate_room_response = self.client.post(
            "/api/v1/admin/room-types/create",
            {
                "hotel": self.hotel.id,
                "name": self.room_type.name,
                "bed_type": self.room_type.bed_type,
                "area": self.room_type.area,
                "breakfast_count": self.room_type.breakfast_count,
                "base_price": str(self.room_type.base_price),
                "max_guest_count": self.room_type.max_guest_count,
                "stock": self.room_type.stock,
                "status": self.room_type.status,
                "description": "重复房型测试",
            },
            format="json",
        )
        self.assertEqual(duplicate_room_response.status_code, 409)
        self.assertEqual(duplicate_room_response.json()["code"], 4090)
        self.assertIn("name", duplicate_room_response.json()["data"]["errors"])

    def test_admin_can_create_employee(self):
        """验证管理员创建员工账号流程。"""
        self.login_admin()
        response = self.client.post(
            "/api/v1/admin/employees/create",
            {
                "username": "frontdesk01",
                "password": "HoteLink#Employee123",
                "name": "前台小王",
                "mobile": "13800138001",
                "role": "hotel_admin",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["role"], "hotel_admin")

    def test_hotel_admin_cannot_access_system_status_or_ai_settings(self):
        """验证酒店管理员无法读取系统状态和 AI 配置。"""
        self.login_hotel_admin()

        system_status = self.client.get("/api/v1/admin/system/status")
        self.assertEqual(system_status.status_code, 403)

        ai_settings = self.client.get("/api/v1/admin/ai/settings")
        self.assertEqual(ai_settings.status_code, 403)

    def test_admin_system_status_should_return_cache_flag(self):
        """验证系统状态接口可返回缓存标记。"""
        self.login_admin()
        cache.clear()

        first_response = self.client.get("/api/v1/admin/system/status")
        self.assertEqual(first_response.status_code, 200)
        self.assertFalse(first_response.json()["data"].get("cached", False))

        cached_response = self.client.get("/api/v1/admin/system/status")
        self.assertEqual(cached_response.status_code, 200)
        self.assertTrue(cached_response.json()["data"].get("cached", False))

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
        self.assertTrue(all("api_key" not in item for item in providers))

    def test_refresh_rotation_and_logout_should_revoke_refresh_token(self):
        """验证 refresh token 轮换后旧 token 失效，登出后当前 token 被吊销。"""
        login_response = self.client.post(
            "/api/v1/public/auth/login",
            {"username": "zhangsan", "password": "Password123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.json()["data"]["access_token"]
        refresh_token = login_response.json()["data"]["refresh_token"]

        refresh_response = self.client.post(
            "/api/v1/public/auth/refresh",
            {"refresh_token": refresh_token},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 200)
        new_refresh_token = refresh_response.json()["data"]["refresh_token"]
        self.assertTrue(new_refresh_token)
        self.assertNotEqual(new_refresh_token, refresh_token)

        old_refresh_retry = self.client.post(
            "/api/v1/public/auth/refresh",
            {"refresh_token": refresh_token},
            format="json",
        )
        self.assertEqual(old_refresh_retry.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_response = self.client.post(
            "/api/v1/user/auth/logout",
            {"refresh_token": new_refresh_token},
            format="json",
        )
        self.assertEqual(logout_response.status_code, 200)
        self.assertTrue(logout_response.json()["data"]["refresh_revoked"])

        revoked_refresh_retry = self.client.post(
            "/api/v1/public/auth/refresh",
            {"refresh_token": new_refresh_token},
            format="json",
        )
        self.assertEqual(revoked_refresh_retry.status_code, 401)

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

    def test_admin_ai_reply_suggestion_should_write_call_log(self):
        """验证评价回复建议调用后会写入 AI 调用日志。"""
        self.login_admin()
        from apps.crm.models import Review

        review = Review.objects.create(
            order=self.order,
            user=self.user,
            hotel=self.hotel,
            score=4,
            content="服务不错，下次还会入住",
        )

        with patch("apps.api.views.AIChatService.is_available", return_value=True), patch(
            "apps.api.views.AIChatService.generate_reply_suggestion",
            return_value={
                "suggestions": [{"style": "formal", "content": "感谢您的反馈，期待再次光临。"}],
                "provider": "testprovider",
                "model_used": "test-chat-model",
                "raw": {"usage": {"prompt_tokens": 12, "completion_tokens": 18, "total_tokens": 30}},
            },
        ):
            response = self.client.post(
                "/api/v1/admin/ai/reply-suggestion",
                {"review_id": review.id},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["code"], 0)
        log = AICallLog.objects.filter(scene="reply_suggestion").order_by("-id").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, AICallLog.STATUS_SUCCESS)
        self.assertGreaterEqual(log.total_tokens, 30)

    def test_admin_ai_provider_switch_then_call_should_work_and_log(self):
        """验证新增并切换 AI 供应商后，AI 接口可调用且会记录日志。"""
        self.login_admin()

        add_response = self.client.post(
            "/api/v1/admin/ai/provider/add",
            {
                "name": "testprovider2",
                "label": "Test Provider 2",
                "base_url": "https://example.com/v1",
                "api_key": "test-key-2",
                "chat_model": "test-chat-model-2",
                "reasoning_model": "test-reasoning-model-2",
            },
            format="json",
        )
        self.assertEqual(add_response.status_code, 200)

        switch_response = self.client.post(
            "/api/v1/admin/ai/provider/switch",
            {"provider_name": "testprovider2"},
            format="json",
        )
        self.assertEqual(switch_response.status_code, 200)
        self.assertEqual(switch_response.json()["data"]["active_provider"], "testprovider2")

        with patch("apps.api.views.AIChatService.is_available", return_value=True), patch(
            "apps.api.views.AIChatService.generate_report_summary",
            return_value={
                "summary": "这是测试摘要",
                "provider": "testprovider2",
                "model_used": "test-chat-model-2",
                "raw": {"usage": {"prompt_tokens": 20, "completion_tokens": 25, "total_tokens": 45}},
            },
        ):
            call_response = self.client.post(
                "/api/v1/admin/ai/report-summary",
                {
                    "start_date": str(timezone.localdate() - timedelta(days=7)),
                    "end_date": str(timezone.localdate()),
                },
                format="json",
            )

        self.assertEqual(call_response.status_code, 200)
        self.assertEqual(call_response.json()["code"], 0)
        self.assertIn("summary", call_response.json()["data"])

        log = AICallLog.objects.filter(scene="report_summary").order_by("-id").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, AICallLog.STATUS_SUCCESS)
        self.assertEqual(log.provider, "testprovider2")
        self.assertEqual(log.model, "test-chat-model-2")

    def test_admin_ai_test_endpoint_should_return_answer_and_write_log(self):
        """验证管理端 AI 测试接口可调用，并写入 admin_ai_test 日志。"""
        self.login_admin()

        with patch("apps.api.views.AIChatService.is_available", return_value=True), patch(
            "apps.api.views.AIChatService.create_chat_completion",
            return_value={
                "provider": "testprovider",
                "model": "test-chat-model",
                "content": "AI测试成功，当前模型 test-chat-model。",
                "raw": {"usage": {"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22}},
            },
        ):
            response = self.client.post(
                "/api/v1/admin/ai/test",
                {"message": "请回复 AI测试成功"},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertIn("AI测试成功", payload["data"]["answer"])

        log = AICallLog.objects.filter(scene="admin_ai_test").order_by("-id").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, AICallLog.STATUS_SUCCESS)
        self.assertEqual(log.provider, "testprovider")
        self.assertEqual(log.model, "test-chat-model")
