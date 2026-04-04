from django.contrib.auth.models import User
from rest_framework import serializers

from apps.bookings.models import BookingOrder
from apps.crm.models import FavoriteHotel, InvoiceRequest, InvoiceTitle, Review, UserCoupon
from apps.hotels.models import Hotel, RoomInventory, RoomType
from apps.operations.models import SystemNotice
from apps.payments.models import PaymentRecord
from apps.reports.models import ReportTask
from apps.users.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
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
            "rating",
            "min_price",
            "status",
            "is_recommended",
        ]


class RoomTypeSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

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
            "description",
        ]


class HotelDetailSerializer(serializers.ModelSerializer):
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
            "rating",
            "min_price",
            "status",
            "is_recommended",
            "room_types",
        ]


class ReviewSerializer(serializers.ModelSerializer):
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
    hotel = HotelSimpleSerializer(read_only=True)

    class Meta:
        model = FavoriteHotel
        fields = ["id", "hotel", "created_at"]


class RoomInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomInventory
        fields = ["id", "room_type", "date", "price", "stock", "status"]


class BookingOrderSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = PaymentRecord
        fields = ["id", "order_id", "payment_no", "method", "status", "amount", "paid_at", "created_at"]


class ReportTaskSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = SystemNotice
        fields = ["id", "notice_type", "title", "content", "is_read", "created_at"]


class RegisterSerializer(serializers.Serializer):
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
    username = serializers.CharField(max_length=150, min_length=3)
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不一致"})
        return attrs


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class ProfileUpdateSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)
    mobile = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=UserProfile.GENDER_CHOICES, required=False)
    birthday = serializers.DateField(required=False, allow_null=True)


class FavoriteActionSerializer(serializers.Serializer):
    hotel_id = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
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
    order_id = serializers.IntegerField(min_value=1)
    guest_name = serializers.CharField(max_length=100, required=False)
    guest_mobile = serializers.CharField(max_length=20, required=False)
    remark = serializers.CharField(max_length=255, required=False, allow_blank=True)


class OrderPaySerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    payment_method = serializers.ChoiceField(choices=PaymentRecord.METHOD_CHOICES)


class OrderCancelSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ReviewCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    score = serializers.IntegerField(min_value=1, max_value=5)
    content = serializers.CharField()


class HotelCreateSerializer(serializers.ModelSerializer):
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
            "rating",
            "min_price",
            "is_recommended",
            "status",
        ]


class HotelUpdateSerializer(HotelCreateSerializer):
    hotel_id = serializers.IntegerField(min_value=1)


class RoomTypeCreateSerializer(serializers.ModelSerializer):
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
            "description",
        ]


class RoomTypeUpdateSerializer(RoomTypeCreateSerializer):
    room_type_id = serializers.IntegerField(min_value=1)


class InventoryUpdateSerializer(serializers.Serializer):
    room_type_id = serializers.IntegerField(min_value=1)
    date = serializers.DateField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField(min_value=0)
    status = serializers.ChoiceField(choices=RoomInventory.STATUS_CHOICES)


class OrderStatusSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    target_status = serializers.ChoiceField(choices=BookingOrder.STATUS_CHOICES)


class CheckInSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    room_no = serializers.CharField(max_length=20)
    operator_remark = serializers.CharField(max_length=255, required=False, allow_blank=True)


class CheckOutSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    consume_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    operator_remark = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ReplyReviewSerializer(serializers.Serializer):
    review_id = serializers.IntegerField(min_value=1)
    content = serializers.CharField()


class ChangeUserStatusSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=UserProfile.STATUS_CHOICES)


class ReportTaskCreateSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=ReportTask.TYPE_CHOICES)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    hotel_id = serializers.IntegerField(required=False, allow_null=True)


class AIChatSerializer(serializers.Serializer):
    scene = serializers.CharField(max_length=50)
    question = serializers.CharField()
    hotel_id = serializers.IntegerField(required=False, allow_null=True)
    order_id = serializers.IntegerField(required=False, allow_null=True)


class AIReportSummarySerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    hotel_id = serializers.IntegerField(required=False, allow_null=True)


class AIReviewSummarySerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    hotel_id = serializers.IntegerField(required=False, allow_null=True)


class AIReplySuggestionSerializer(serializers.Serializer):
    review_id = serializers.IntegerField(min_value=1)


class ReportTaskCreateSimpleSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=ReportTask.TYPE_CHOICES)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    hotel_id = serializers.IntegerField(required=False, allow_null=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": ["两次输入的新密码不一致"]})
        return attrs


class UploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    scene = serializers.CharField(max_length=50)


class InvoiceTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceTitle
        fields = ["id", "invoice_type", "title", "tax_no", "email", "created_at"]


class InvoiceTitleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceTitle
        fields = ["invoice_type", "title", "tax_no", "email"]


class InvoiceApplySerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    invoice_title_id = serializers.IntegerField(min_value=1)


class InvoiceRequestSerializer(serializers.ModelSerializer):
    invoice_title = InvoiceTitleSerializer(read_only=True)

    class Meta:
        model = InvoiceRequest
        fields = ["id", "order_id", "status", "invoice_title", "created_at"]


class UserCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCoupon
        fields = ["id", "name", "amount", "status", "valid_start", "valid_end", "created_at"]


class EmployeeCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(max_length=100)
    mobile = serializers.CharField(max_length=20)
    role = serializers.ChoiceField(choices=[("hotel_admin", "酒店管理员"), ("system_admin", "系统管理员")])


class SettingsUpdateSerializer(serializers.Serializer):
    platform_name = serializers.CharField(max_length=100, required=False)
    support_phone = serializers.CharField(max_length=30, required=False)
    order_auto_cancel_minutes = serializers.IntegerField(min_value=1, required=False)


class AISettingsUpdateSerializer(serializers.Serializer):
    ai_enabled = serializers.BooleanField(required=False)
    default_scene = serializers.CharField(max_length=50, required=False)
