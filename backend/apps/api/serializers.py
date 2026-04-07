"""apps/api/serializers.py —— API 请求与响应序列化定义。"""

from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import serializers
from urllib.parse import quote, urlparse

from apps.bookings.models import BookingOrder
from apps.crm.models import FavoriteHotel, InvoiceRequest, InvoiceTitle, Review, UserCoupon
from apps.hotels.models import Hotel, RoomInventory, RoomType
from apps.operations.models import SystemNotice
from apps.payments.models import PaymentRecord
from apps.reports.models import ReportTask
from apps.users.models import UserProfile


def build_thumb_proxy_url(url: str | None, width: int = 56, height: int = 40) -> str:
    if not url:
        return ""
    raw = str(url)
    media_path = raw
    if raw.startswith("http://") or raw.startswith("https://"):
        media_path = urlparse(raw).path or ""
    if not media_path.startswith(settings.MEDIA_URL):
        return raw
    return f"/api/v1/common/image-thumb?url={quote(media_path, safe='')}&w={width}&h={height}"


class UserProfileSerializer(serializers.ModelSerializer):
    """UserProfile 序列化器：用于接口参数校验或响应数据转换。"""
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "email",
            "nickname",
            "avatar",
            "mobile",
            "gender",
            "birthday",
            "role",
            "status",
            "member_level",
            "points",
        ]


class HotelSimpleSerializer(serializers.ModelSerializer):
    """HotelSimple 序列化器：用于接口参数校验或响应数据转换。"""
    cover_thumb = serializers.SerializerMethodField()

    def get_cover_thumb(self, obj):
        width = int(self.context.get("thumb_width", 56))
        height = int(self.context.get("thumb_height", 40))
        return build_thumb_proxy_url(getattr(obj, "cover_image", ""), width=width, height=height)

    class Meta:
        model = Hotel
        fields = [
            "id",
            "name",
            "city",
            "address",
            "star",
            "phone",
            "cover_image",
            "cover_thumb",
            "images",
            "rating",
            "min_price",
            "status",
            "is_recommended",
        ]


class RoomTypeSerializer(serializers.ModelSerializer):
    """RoomType 序列化器：用于接口参数校验或响应数据转换。"""
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    image_thumb = serializers.SerializerMethodField()

    def get_image_thumb(self, obj):
        width = int(self.context.get("thumb_width", 56))
        height = int(self.context.get("thumb_height", 40))
        return build_thumb_proxy_url(getattr(obj, "image", ""), width=width, height=height)

    class Meta:
        model = RoomType
        fields = [
            "id",
            "hotel",
            "hotel_name",
            "name",
            "bed_type",
            "area",
            "breakfast_count",
            "base_price",
            "max_guest_count",
            "stock",
            "status",
            "image",
            "image_thumb",
            "description",
        ]


class HotelDetailSerializer(serializers.ModelSerializer):
    """HotelDetail 序列化器：用于接口参数校验或响应数据转换。"""
    room_types = RoomTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Hotel
        fields = [
            "id",
            "name",
            "city",
            "address",
            "star",
            "phone",
            "description",
            "cover_image",
            "images",
            "rating",
            "min_price",
            "status",
            "is_recommended",
            "room_types",
        ]


class ReviewSerializer(serializers.ModelSerializer):
    """Review 序列化器：用于接口参数校验或响应数据转换。"""
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "order_id",
            "hotel_id",
            "username",
            "score",
            "content",
            "reply_content",
            "created_at",
        ]


class FavoriteHotelSerializer(serializers.ModelSerializer):
    """FavoriteHotel 序列化器：用于接口参数校验或响应数据转换。"""
    hotel = HotelSimpleSerializer(read_only=True)

    class Meta:
        model = FavoriteHotel
        fields = ["id", "hotel", "created_at"]


class RoomInventorySerializer(serializers.ModelSerializer):
    """RoomInventory 序列化器：用于接口参数校验或响应数据转换。"""
    class Meta:
        model = RoomInventory
        fields = ["id", "room_type", "date", "price", "stock", "status"]


class BookingOrderSerializer(serializers.ModelSerializer):
    """BookingOrder 序列化器：用于接口参数校验或响应数据转换。"""
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)

    class Meta:
        model = BookingOrder
        fields = [
            "id",
            "order_no",
            "hotel",
            "hotel_name",
            "room_type",
            "room_type_name",
            "status",
            "payment_status",
            "check_in_date",
            "check_out_date",
            "guest_name",
            "guest_mobile",
            "guest_count",
            "room_no",
            "remark",
            "operator_remark",
            "original_amount",
            "discount_amount",
            "pay_amount",
            "created_at",
        ]


class PaymentRecordSerializer(serializers.ModelSerializer):
    """PaymentRecord 序列化器：用于接口参数校验或响应数据转换。"""
    class Meta:
        model = PaymentRecord
        fields = ["id", "order_id", "payment_no", "method", "status", "amount", "paid_at", "created_at"]


class ReportTaskSerializer(serializers.ModelSerializer):
    """ReportTask 序列化器：用于接口参数校验或响应数据转换。"""
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

    class Meta:
        model = ReportTask
        fields = [
            "id",
            "hotel",
            "hotel_name",
            "report_type",
            "start_date",
            "end_date",
            "status",
            "result_summary",
            "created_at",
        ]


class SystemNoticeSerializer(serializers.ModelSerializer):
    """SystemNotice 序列化器：用于接口参数校验或响应数据转换。"""
    class Meta:
        model = SystemNotice
        fields = ["id", "notice_type", "title", "content", "is_read", "created_at"]


class RegisterSerializer(serializers.Serializer):
    """Register 序列化器：用于接口参数校验或响应数据转换。"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    mobile = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": ["两次输入的密码不一致"]})
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": ["用户名已存在"]})
        return attrs


class InitSetupSerializer(serializers.Serializer):
    """InitSetup 序列化器：用于接口参数校验或响应数据转换。"""
    username = serializers.CharField(max_length=150, min_length=3)
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不一致"})
        return attrs


class LoginSerializer(serializers.Serializer):
    """Login 序列化器：用于接口参数校验或响应数据转换。"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class ProfileUpdateSerializer(serializers.Serializer):
    """ProfileUpdate 序列化器：用于接口参数校验或响应数据转换。"""
    nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)
    mobile = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=UserProfile.GENDER_CHOICES, required=False)
    birthday = serializers.DateField(required=False, allow_null=True)


class FavoriteActionSerializer(serializers.Serializer):
    """FavoriteAction 序列化器：用于接口参数校验或响应数据转换。"""
    hotel_id = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    """OrderCreate 序列化器：用于接口参数校验或响应数据转换。"""
    hotel_id = serializers.IntegerField(min_value=1)
    room_type_id = serializers.IntegerField(min_value=1)
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()
    guest_name = serializers.CharField(max_length=100)
    guest_mobile = serializers.CharField(max_length=20)
    guest_count = serializers.IntegerField(min_value=1)
    coupon_id = serializers.IntegerField(required=False, allow_null=True)
    remark = serializers.CharField(max_length=255, required=False, allow_blank=True)


class OrderUpdateSerializer(serializers.Serializer):
    """OrderUpdate 序列化器：用于接口参数校验或响应数据转换。"""
    order_id = serializers.IntegerField(min_value=1)
    guest_name = serializers.CharField(max_length=100, required=False)
    guest_mobile = serializers.CharField(max_length=20, required=False)
    remark = serializers.CharField(max_length=255, required=False, allow_blank=True)


class OrderPaySerializer(serializers.Serializer):
    """OrderPay 序列化器：用于接口参数校验或响应数据转换。"""
    order_id = serializers.IntegerField(min_value=1)
    payment_method = serializers.ChoiceField(choices=PaymentRecord.METHOD_CHOICES)


class OrderCancelSerializer(serializers.Serializer):
    """OrderCancel 序列化器：用于接口参数校验或响应数据转换。"""
    order_id = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ReviewCreateSerializer(serializers.Serializer):
    """ReviewCreate 序列化器：用于接口参数校验或响应数据转换。"""
    order_id = serializers.IntegerField(min_value=1)
    score = serializers.IntegerField(min_value=1, max_value=5)
    content = serializers.CharField()


class HotelCreateSerializer(serializers.ModelSerializer):
    """HotelCreate 序列化器：用于接口参数校验或响应数据转换。"""
    class Meta:
        model = Hotel
        fields = [
            "name",
            "city",
            "address",
            "star",
            "phone",
            "description",
            "cover_image",
            "images",
            "rating",
            "min_price",
            "is_recommended",
            "status",
        ]


class HotelUpdateSerializer(HotelCreateSerializer):
    """HotelUpdate 序列化器：用于接口参数校验或响应数据转换。"""
    hotel_id = serializers.IntegerField(min_value=1)


class RoomTypeCreateSerializer(serializers.ModelSerializer):
    """RoomTypeCreate 序列化器：用于接口参数校验或响应数据转换。"""
    class Meta:
        model = RoomType
        fields = [
            "hotel",
            "name",
            "bed_type",
            "area",
            "breakfast_count",
            "base_price",
            "max_guest_count",
            "stock",
            "status",
            "image",
            "description",
        ]


class RoomTypeUpdateSerializer(RoomTypeCreateSerializer):
    """RoomTypeUpdate 序列化器：用于接口参数校验或响应数据转换。"""
    room_type_id = serializers.IntegerField(min_value=1)


class InventoryUpdateSerializer(serializers.Serializer):
    """InventoryUpdate 序列化器：用于接口参数校验或响应数据转换。"""
    room_type_id = serializers.IntegerField(min_value=1)
    date = serializers.DateField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField(min_value=0)
    status = serializers.ChoiceField(choices=RoomInventory.STATUS_CHOICES)


class OrderStatusSerializer(serializers.Serializer):
    """OrderStatus 序列化器：用于接口参数校验或响应数据转换。"""
    order_id = serializers.IntegerField(min_value=1)
    target_status = serializers.ChoiceField(choices=BookingOrder.STATUS_CHOICES)


class CheckInSerializer(serializers.Serializer):
    """CheckIn 序列化器：用于接口参数校验或响应数据转换。"""
    order_id = serializers.IntegerField(min_value=1)
    room_no = serializers.CharField(max_length=20)
    operator_remark = serializers.CharField(max_length=255, required=False, allow_blank=True)


class CheckOutSerializer(serializers.Serializer):
    """CheckOut 序列化器：用于接口参数校验或响应数据转换。"""
    order_id = serializers.IntegerField(min_value=1)
    consume_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    operator_remark = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ReplyReviewSerializer(serializers.Serializer):
    """ReplyReview 序列化器：用于接口参数校验或响应数据转换。"""
    review_id = serializers.IntegerField(min_value=1)
    content = serializers.CharField()


class ChangeUserStatusSerializer(serializers.Serializer):
    """ChangeUserStatus 序列化器：用于接口参数校验或响应数据转换。"""
    user_id = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=UserProfile.STATUS_CHOICES)


class ReportTaskCreateSerializer(serializers.Serializer):
    """ReportTaskCreate 序列化器：用于接口参数校验或响应数据转换。"""
    report_type = serializers.ChoiceField(choices=ReportTask.TYPE_CHOICES)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    hotel_id = serializers.IntegerField(required=False, allow_null=True)


class AIChatSerializer(serializers.Serializer):
    """AIChat 序列化器：用于接口参数校验或响应数据转换。"""
    scene = serializers.CharField(max_length=50)
    question = serializers.CharField()
    hotel_id = serializers.IntegerField(required=False, allow_null=True)
    order_id = serializers.IntegerField(required=False, allow_null=True)
    booking_context = serializers.JSONField(required=False)


class AIReportSummarySerializer(serializers.Serializer):
    """AIReportSummary 序列化器：用于接口参数校验或响应数据转换。"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    hotel_id = serializers.IntegerField(required=False, allow_null=True)


class AIReviewSummarySerializer(serializers.Serializer):
    """AIReviewSummary 序列化器：用于接口参数校验或响应数据转换。"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    hotel_id = serializers.IntegerField(required=False, allow_null=True)


class AIReplySuggestionSerializer(serializers.Serializer):
    """AIReplySuggestion 序列化器：用于接口参数校验或响应数据转换。"""
    review_id = serializers.IntegerField(min_value=1)


class ReportTaskCreateSimpleSerializer(serializers.Serializer):
    """ReportTaskCreateSimple 序列化器：用于接口参数校验或响应数据转换。"""
    report_type = serializers.ChoiceField(choices=ReportTask.TYPE_CHOICES)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    hotel_id = serializers.IntegerField(required=False, allow_null=True)


class PasswordChangeSerializer(serializers.Serializer):
    """PasswordChange 序列化器：用于接口参数校验或响应数据转换。"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": ["两次输入的新密码不一致"]})
        return attrs


class UploadSerializer(serializers.Serializer):
    """Upload 序列化器：用于接口参数校验或响应数据转换。"""
    file = serializers.FileField()
    scene = serializers.CharField(max_length=50)


class InvoiceTitleSerializer(serializers.ModelSerializer):
    """InvoiceTitle 序列化器：用于接口参数校验或响应数据转换。"""
    class Meta:
        model = InvoiceTitle
        fields = ["id", "invoice_type", "title", "tax_no", "email", "created_at"]


class InvoiceTitleCreateSerializer(serializers.ModelSerializer):
    """InvoiceTitleCreate 序列化器：用于接口参数校验或响应数据转换。"""
    class Meta:
        model = InvoiceTitle
        fields = ["invoice_type", "title", "tax_no", "email"]


class InvoiceApplySerializer(serializers.Serializer):
    """InvoiceApply 序列化器：用于接口参数校验或响应数据转换。"""
    order_id = serializers.IntegerField(min_value=1)
    invoice_title_id = serializers.IntegerField(min_value=1)


class InvoiceRequestSerializer(serializers.ModelSerializer):
    """InvoiceRequest 序列化器：用于接口参数校验或响应数据转换。"""
    invoice_title = InvoiceTitleSerializer(read_only=True)

    class Meta:
        model = InvoiceRequest
        fields = ["id", "order_id", "status", "invoice_title", "created_at"]


class UserCouponSerializer(serializers.ModelSerializer):
    """UserCoupon 序列化器：用于接口参数校验或响应数据转换。"""
    class Meta:
        model = UserCoupon
        fields = ["id", "name", "amount", "status", "valid_start", "valid_end", "created_at"]


class EmployeeCreateSerializer(serializers.Serializer):
    """EmployeeCreate 序列化器：用于接口参数校验或响应数据转换。"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(max_length=100)
    mobile = serializers.CharField(max_length=20)
    role = serializers.ChoiceField(choices=[("hotel_admin", "酒店管理员"), ("system_admin", "系统管理员")])


class SettingsUpdateSerializer(serializers.Serializer):
    """SettingsUpdate 序列化器：用于接口参数校验或响应数据转换。"""
    platform_name = serializers.CharField(max_length=100, required=False)
    support_phone = serializers.CharField(max_length=30, required=False)
    order_auto_cancel_minutes = serializers.IntegerField(min_value=1, required=False)


class AISettingsUpdateSerializer(serializers.Serializer):
    """AISettingsUpdate 序列化器：支持多供应商配置更新。"""
    ai_enabled = serializers.BooleanField(required=False)
    active_provider = serializers.CharField(max_length=50, required=False)
    providers = serializers.ListField(child=serializers.DictField(), required=False)


class AIProviderCreateSerializer(serializers.Serializer):
    """AIProviderCreate 序列化器：新增或编辑单个 AI 供应商。"""
    name = serializers.CharField(max_length=50)
    label = serializers.CharField(max_length=100, required=False)
    base_url = serializers.URLField()
    api_key = serializers.CharField(max_length=500, required=False, allow_blank=True)
    chat_model = serializers.CharField(max_length=100)
    reasoning_model = serializers.CharField(max_length=100, required=False, allow_blank=True)
    timeout = serializers.FloatField(min_value=1, max_value=300, required=False, default=60)


class AIProviderSwitchSerializer(serializers.Serializer):
    """AIProviderSwitch 序列化器：切换活跃供应商。"""
    provider_name = serializers.CharField(max_length=50)


class AIProviderDeleteSerializer(serializers.Serializer):
    """AIProviderDelete 序列化器：删除供应商。"""
    provider_name = serializers.CharField(max_length=50)


class SystemResetSerializer(serializers.Serializer):
    """SystemReset 序列化器：系统重置确认。"""
    confirm = serializers.CharField()

    def validate_confirm(self, value: str) -> str:
        if value != "RESET":
            raise serializers.ValidationError("请输入 RESET 以确认重置操作")
        return value
