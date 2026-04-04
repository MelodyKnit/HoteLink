from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.files.storage import default_storage
from django.db.models import Avg, Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.crypto import get_random_string
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.api.permissions import IsAdminRole
from apps.api.responses import api_response, paginated_response
from apps.api.serializers import (
    AIChatSerializer,
    AIReplySuggestionSerializer,
    AIReportSummarySerializer,
    AIReviewSummarySerializer,
    AISettingsUpdateSerializer,
    BookingOrderSerializer,
    ChangeUserStatusSerializer,
    CheckInSerializer,
    CheckOutSerializer,
    EmployeeCreateSerializer,
    FavoriteActionSerializer,
    FavoriteHotelSerializer,
    HotelCreateSerializer,
    HotelDetailSerializer,
    HotelSimpleSerializer,
    HotelUpdateSerializer,
    InvoiceApplySerializer,
    InvoiceRequestSerializer,
    InvoiceTitleCreateSerializer,
    InvoiceTitleSerializer,
    InventoryUpdateSerializer,
    LoginSerializer,
    OrderCancelSerializer,
    OrderCreateSerializer,
    OrderPaySerializer,
    OrderStatusSerializer,
    OrderUpdateSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ReplyReviewSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
    ReportTaskCreateSimpleSerializer,
    RoomInventorySerializer,
    RoomTypeCreateSerializer,
    RoomTypeSerializer,
    RoomTypeUpdateSerializer,
    SettingsUpdateSerializer,
    SystemNoticeSerializer,
    UploadSerializer,
    UserCouponSerializer,
    UserProfileSerializer,
)
from apps.bookings.models import BookingOrder
from apps.crm.models import FavoriteHotel, InvoiceRequest, InvoiceTitle, Review, UserCoupon
from apps.hotels.models import Hotel, RoomInventory, RoomType
from apps.operations.models import SystemNotice
from apps.operations.services.ai_service import AIChatService
from apps.payments.models import PaymentRecord
from apps.reports.models import ReportTask
from apps.users.models import UserProfile

User = get_user_model()


def ensure_profile(user: User) -> UserProfile:
    defaults = {
        "nickname": user.username,
        "mobile": "",
        "role": UserProfile.ROLE_SYSTEM_ADMIN if user.is_superuser else UserProfile.ROLE_USER,
        "status": UserProfile.STATUS_ACTIVE,
    }
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults=defaults)
    return profile


def get_page_params(request) -> tuple[int, int]:
    try:
        page = max(int(request.query_params.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.query_params.get("page_size", 20))
    except (TypeError, ValueError):
        page_size = 20
    page_size = min(max(page_size, 1), 100)
    return page, page_size


def paginate_queryset(queryset, page: int, page_size: int):
    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    return queryset[start:end], total


def build_tokens_for_user(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "token_type": "Bearer",
        "expires_in": 60 * 60 * 2,
    }


def make_order_no() -> str:
    now = timezone.localtime()
    return f"HT{now.strftime('%Y%m%d%H%M%S')}{get_random_string(4, allowed_chars='0123456789')}"


def make_payment_no() -> str:
    now = timezone.localtime()
    return f"PM{now.strftime('%Y%m%d%H%M%S')}{get_random_string(4, allowed_chars='0123456789')}"


def fallback_ai_reply(scene: str) -> str:
    if scene == "customer_service":
        return "您好，这里是智能客服助手。当前系统尚未接入真实 AI 服务，我可以先返回基础说明，建议后续接入 DeepSeek 后提供更准确回答。"
    if scene == "report_summary":
        return "当前时间段内营收与订单波动建议结合入住率、取消率和均价变化综合判断。"
    if scene == "review_summary":
        return "近期评价主要关注服务体验、卫生情况和入住便利性，建议优先处理重复出现的问题。"
    if scene == "reply_suggestion":
        return "感谢您的反馈，我们会认真优化相关体验，期待您的再次入住。"
    return f"当前为 {scene} 场景的占位回复。"


def get_dict_payload() -> dict:
    return {
        "hotel_star": [{"label": f"{i} 星", "value": i} for i in [2, 3, 4, 5]],
        "payment_method": [
            {"label": "模拟支付", "value": "mock"},
            {"label": "微信支付", "value": "wechat"},
            {"label": "支付宝", "value": "alipay"},
            {"label": "现金", "value": "cash"},
            {"label": "银行卡", "value": "card"},
        ],
        "bed_type": [
            {"label": "单人床", "value": "single"},
            {"label": "双人床", "value": "double"},
            {"label": "大床", "value": "queen"},
            {"label": "双床", "value": "twin"},
            {"label": "家庭床", "value": "family"},
        ],
    }


class ApiRootView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return api_response(
            data={
                "name": "HoteLink API",
                "version": "v1",
                "user_api_base": "/api/v1/user/",
                "admin_api_base": "/api/v1/admin/",
            }
        )


class UserRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)

        data = serializer.validated_data
        user = User.objects.create_user(
            username=data["username"],
            password=data["password"],
            email=data.get("email", ""),
        )
        UserProfile.objects.create(
            user=user,
            nickname=data["username"],
            mobile=data["mobile"],
        )
        return api_response(data={"user_id": user.id, "username": user.username})


class BaseLoginView(APIView):
    permission_classes = [AllowAny]
    required_roles: set[str] | None = None

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)

        user = authenticate(
            request=request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return api_response(code=4010, message="用户名或密码错误", data=None, status_code=401)

        profile = ensure_profile(user)
        if self.required_roles and profile.role not in self.required_roles and not user.is_superuser:
            return api_response(code=4030, message="permission denied", data=None, status_code=403)

        tokens = build_tokens_for_user(user)
        return api_response(
            data={
                **tokens,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": profile.role,
                },
            }
        )


class UserLoginView(BaseLoginView):
    required_roles = {"user", "hotel_admin", "system_admin"}


class AdminLoginView(BaseLoginView):
    required_roles = {"hotel_admin", "system_admin"}


class RefreshTokenApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return api_response(code=4002, message="缺少 refresh_token", data=None, status_code=400)
        try:
            refresh = RefreshToken(refresh_token)
            return api_response(
                data={
                    "access_token": str(refresh.access_token),
                    "token_type": "Bearer",
                }
            )
        except Exception:
            return api_response(code=4011, message="Token 无效", data=None, status_code=401)


class LogoutApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return api_response(data={"logged_out": True})


class UserAuthMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ensure_profile(request.user)
        return api_response(data=UserProfileSerializer(profile).data)


class CommonCitiesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cities = list(Hotel.objects.exclude(city="").values_list("city", flat=True).distinct().order_by("city"))
        return api_response(data={"items": [{"label": city, "value": city} for city in cities]})


class CommonDictsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        requested = request.query_params.get("types", "")
        payload = get_dict_payload()
        if not requested:
            return api_response(data=payload)
        result = {}
        for key in [item.strip() for item in requested.split(",") if item.strip()]:
            if key in payload:
                result[key] = payload[key]
        return api_response(data=result)


class CommonUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        file_obj = serializer.validated_data["file"]
        scene = serializer.validated_data["scene"]
        path = default_storage.save(f"uploads/{scene}/{file_obj.name}", file_obj)
        file_url = request.build_absolute_uri(f"/media/{path}")
        return api_response(data={"file_name": file_obj.name, "file_url": file_url, "scene": scene})


class PublicHomeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        recommended_hotels = Hotel.objects.filter(status=Hotel.STATUS_ONLINE).order_by("-is_recommended", "-id")[:5]
        recommended_room_types = RoomType.objects.filter(status=RoomType.STATUS_ONLINE).select_related("hotel")[:5]
        return api_response(
            data={
                "banners": [
                    {"id": 1, "title": "精选酒店", "image_url": "", "link": "/hotels"},
                ],
                "recommended_hotels": HotelSimpleSerializer(recommended_hotels, many=True).data,
                "recommended_room_types": RoomTypeSerializer(recommended_room_types, many=True).data,
                "activities": [
                    {"id": 1, "title": "春季特惠", "description": "部分酒店限时折扣"},
                ],
            }
        )


class PublicHotelsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Hotel.objects.filter(status=Hotel.STATUS_ONLINE)
        keyword = request.query_params.get("keyword")
        city = request.query_params.get("city")
        star = request.query_params.get("star")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        sort = request.query_params.get("sort", "default")

        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(address__icontains=keyword))
        if city:
            queryset = queryset.filter(city=city)
        if star:
            queryset = queryset.filter(star=star)
        if min_price:
            queryset = queryset.filter(min_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(min_price__lte=max_price)

        order_mapping = {
            "price_asc": "min_price",
            "price_desc": "-min_price",
            "rating_desc": "-rating",
            "popular_desc": "-is_recommended",
            "default": "-id",
        }
        queryset = queryset.order_by(order_mapping.get(sort, "-id"))

        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(
            items=HotelSimpleSerializer(page_queryset, many=True).data,
            page=page,
            page_size=page_size,
            total=total,
        )


class PublicHotelSearchSuggestView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        keyword = request.query_params.get("keyword", "").strip()
        if not keyword:
            return api_response(data={"items": []})
        hotels = Hotel.objects.filter(status=Hotel.STATUS_ONLINE, name__icontains=keyword).order_by("-is_recommended", "name")[:10]
        items = [{"hotel_id": hotel.id, "name": hotel.name, "city": hotel.city} for hotel in hotels]
        return api_response(data={"items": items})


class PublicHotelDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        hotel_id = request.query_params.get("hotel_id")
        if not hotel_id:
            return api_response(code=4002, message="缺少 hotel_id", data=None, status_code=400)
        try:
            hotel = Hotel.objects.prefetch_related("room_types").get(pk=hotel_id)
        except Hotel.DoesNotExist:
            return api_response(code=4040, message="酒店不存在", data=None, status_code=404)
        return api_response(data=HotelDetailSerializer(hotel).data)


class PublicHotelReviewsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        hotel_id = request.query_params.get("hotel_id")
        if not hotel_id:
            return api_response(code=4002, message="缺少 hotel_id", data=None, status_code=400)
        queryset = Review.objects.filter(hotel_id=hotel_id).select_related("user")
        score = request.query_params.get("score")
        if score:
            queryset = queryset.filter(score=score)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(
            items=ReviewSerializer(page_queryset, many=True).data,
            page=page,
            page_size=page_size,
            total=total,
        )


class PublicRoomTypeCalendarView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        room_type_id = request.query_params.get("room_type_id")
        start_date = parse_date(request.query_params.get("start_date", ""))
        end_date = parse_date(request.query_params.get("end_date", ""))
        if not room_type_id or not start_date or not end_date:
            return api_response(code=4001, message="room_type_id/start_date/end_date 参数不完整", data=None, status_code=400)

        queryset = RoomInventory.objects.filter(
            room_type_id=room_type_id,
            date__gte=start_date,
            date__lte=end_date,
        ).order_by("date")
        if queryset.exists():
            serializer_data = RoomInventorySerializer(queryset, many=True).data
        else:
            room_type = RoomType.objects.filter(pk=room_type_id).first()
            if not room_type:
                return api_response(code=4040, message="房型不存在", data=None, status_code=404)
            serializer_data = []
            current = start_date
            while current <= end_date:
                serializer_data.append(
                    {
                        "room_type": room_type.id,
                        "date": current,
                        "price": room_type.base_price,
                        "stock": room_type.stock,
                        "status": RoomInventory.STATUS_AVAILABLE,
                    }
                )
                current += timedelta(days=1)

        return api_response(data={"room_type_id": int(room_type_id), "calendar": serializer_data})


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return api_response(data=UserProfileSerializer(ensure_profile(request.user)).data)

    def post(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        profile = ensure_profile(request.user)
        validated = serializer.validated_data
        for field in ["nickname", "mobile", "gender", "birthday"]:
            if field in validated:
                setattr(profile, field, validated[field])
        if "email" in validated:
            request.user.email = validated["email"]
            request.user.save(update_fields=["email"])
        profile.save()
        return api_response(data=UserProfileSerializer(profile).data)


class UserProfileAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get("avatar")
        if not file_obj:
            return api_response(code=4002, message="缺少 avatar", data=None, status_code=400)
        path = default_storage.save(f"avatars/{request.user.id}/{file_obj.name}", file_obj)
        profile = ensure_profile(request.user)
        profile.avatar = request.build_absolute_uri(f"/media/{path}")
        profile.save(update_fields=["avatar", "updated_at"])
        return api_response(data={"avatar": profile.avatar})


class UserPasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        if not request.user.check_password(data["old_password"]):
            return api_response(code=4001, message="旧密码不正确", data=None, status_code=400)
        request.user.set_password(data["new_password"])
        request.user.save()
        return api_response(data={"changed": True})


class UserFavoritesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page, page_size = get_page_params(request)
        queryset = FavoriteHotel.objects.filter(user=request.user).select_related("hotel")
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(
            items=FavoriteHotelSerializer(page_queryset, many=True).data,
            page=page,
            page_size=page_size,
            total=total,
        )

    def post(self, request):
        serializer = FavoriteActionSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        hotel = Hotel.objects.filter(pk=serializer.validated_data["hotel_id"]).first()
        if not hotel:
            return api_response(code=4040, message="酒店不存在", data=None, status_code=404)

        if request.path.endswith("/add"):
            favorite, _ = FavoriteHotel.objects.get_or_create(user=request.user, hotel=hotel)
            return api_response(data={"favorite_id": favorite.id, "hotel_id": hotel.id})
        FavoriteHotel.objects.filter(user=request.user, hotel=hotel).delete()
        return api_response(data={"hotel_id": hotel.id, "removed": True})


class UserOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = BookingOrder.objects.filter(user=request.user).select_related("hotel", "room_type")
        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(
            items=BookingOrderSerializer(page_queryset, many=True).data,
            page=page,
            page_size=page_size,
            total=total,
        )


class UserOrdersDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        order_id = request.query_params.get("order_id")
        if not order_id:
            return api_response(code=4002, message="缺少 order_id", data=None, status_code=400)
        order = BookingOrder.objects.filter(id=order_id, user=request.user).select_related("hotel", "room_type").first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        return api_response(data=BookingOrderSerializer(order).data)


class UserOrdersCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)

        data = serializer.validated_data
        hotel = Hotel.objects.filter(pk=data["hotel_id"]).first()
        room_type = RoomType.objects.filter(pk=data["room_type_id"], hotel_id=data["hotel_id"]).first()
        if not hotel or not room_type:
            return api_response(code=4040, message="酒店或房型不存在", data=None, status_code=404)

        nights = (data["check_out_date"] - data["check_in_date"]).days
        if nights <= 0:
            return api_response(code=4001, message="离店日期必须大于入住日期", data=None, status_code=400)
        original_amount = room_type.base_price * nights
        discount_amount = Decimal("50.00") if data.get("coupon_id") else Decimal("0.00")
        pay_amount = max(original_amount - discount_amount, Decimal("0.00"))

        order = BookingOrder.objects.create(
            user=request.user,
            hotel=hotel,
            room_type=room_type,
            order_no=make_order_no(),
            check_in_date=data["check_in_date"],
            check_out_date=data["check_out_date"],
            guest_name=data["guest_name"],
            guest_mobile=data["guest_mobile"],
            guest_count=data["guest_count"],
            remark=data.get("remark", ""),
            original_amount=original_amount,
            discount_amount=discount_amount,
            pay_amount=pay_amount,
        )

        SystemNotice.objects.create(
            user=request.user,
            notice_type=SystemNotice.TYPE_ORDER,
            title="订单创建成功",
            content=f"订单 {order.order_no} 已创建，请尽快完成支付。",
        )

        return api_response(
            data={
                "order_id": order.id,
                "order_no": order.order_no,
                "status": order.status,
                "payment_status": order.payment_status,
                "original_amount": order.original_amount,
                "discount_amount": order.discount_amount,
                "pay_amount": order.pay_amount,
            }
        )


class UserOrdersUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"], user=request.user).first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        for field in ["guest_name", "guest_mobile", "remark"]:
            if field in data:
                setattr(order, field, data[field])
        order.save()
        return api_response(data=BookingOrderSerializer(order).data)


class UserOrdersPayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderPaySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"], user=request.user).first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        if order.payment_status == BookingOrder.PAYMENT_PAID:
            return api_response(code=4093, message="订单已支付", data=None, status_code=409)

        payment = PaymentRecord.objects.create(
            order=order,
            payment_no=make_payment_no(),
            method=data["payment_method"],
            status=PaymentRecord.STATUS_PAID,
            amount=order.pay_amount,
            paid_at=timezone.now(),
        )
        order.payment_status = BookingOrder.PAYMENT_PAID
        order.status = BookingOrder.STATUS_PAID
        order.save(update_fields=["payment_status", "status", "updated_at"])
        SystemNotice.objects.create(
            user=request.user,
            notice_type=SystemNotice.TYPE_PAYMENT,
            title="支付成功",
            content=f"订单 {order.order_no} 已完成支付。",
        )
        return api_response(data={"order_id": order.id, "payment_id": payment.id, "payment_status": order.payment_status})


class UserOrdersCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCancelSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"], user=request.user).first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        if order.status in {BookingOrder.STATUS_COMPLETED, BookingOrder.STATUS_CANCELLED, BookingOrder.STATUS_CHECKED_IN}:
            return api_response(code=4093, message="当前状态不允许取消", data=None, status_code=409)
        order.status = BookingOrder.STATUS_CANCELLED
        order.operator_remark = data.get("reason", "")
        order.save(update_fields=["status", "operator_remark", "updated_at"])
        return api_response(data={"order_id": order.id, "status": order.status})


class UserReviewsCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"], user=request.user).select_related("hotel").first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        review, created = Review.objects.update_or_create(
            order=order,
            defaults={
                "user": request.user,
                "hotel": order.hotel,
                "score": data["score"],
                "content": data["content"],
            },
        )
        if created:
            profile = ensure_profile(request.user)
            profile.points += 10
            profile.save(update_fields=["points", "updated_at"])
        return api_response(data={"review_id": review.id, "score": review.score})


class UserPointsLogsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ensure_profile(request.user)
        items = []
        if profile.points:
            items.append(
                {
                    "type": "review_reward",
                    "points": profile.points,
                    "description": "累计积分奖励",
                    "created_at": timezone.localtime().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        return api_response(data={"current_points": profile.points, "items": items})


class UserNoticesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page, page_size = get_page_params(request)
        queryset = SystemNotice.objects.filter(user=request.user)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(
            items=SystemNoticeSerializer(page_queryset, many=True).data,
            page=page,
            page_size=page_size,
            total=total,
        )


class UserCouponsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = UserCoupon.objects.filter(user=request.user)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=UserCouponSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)


class UserInvoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = InvoiceRequest.objects.filter(invoice_title__user=request.user).select_related("invoice_title")
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=InvoiceRequestSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)


class UserInvoiceTitleCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InvoiceTitleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        title = serializer.save(user=request.user)
        return api_response(data=InvoiceTitleSerializer(title).data)


class UserInvoiceApplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InvoiceApplySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"], user=request.user).first()
        title = InvoiceTitle.objects.filter(id=data["invoice_title_id"], user=request.user).first()
        if not order or not title:
            return api_response(code=4040, message="订单或发票抬头不存在", data=None, status_code=404)
        invoice_request = InvoiceRequest.objects.create(order=order, invoice_title=title)
        return api_response(data=InvoiceRequestSerializer(invoice_request).data)


class UserAIChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AIChatSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        try:
            if service.is_available():
                result = service.create_chat_completion(
                    [
                        {"role": "system", "content": "你是酒店管理系统的中文客服助手，请用简洁专业的语气回答。"},
                        {"role": "user", "content": data["question"]},
                    ]
                )
                answer = result["content"]
            else:
                answer = fallback_ai_reply(data["scene"])
        except Exception:
            answer = fallback_ai_reply(data["scene"])
        return api_response(data={"answer": answer, "scene": data["scene"]})


class AdminDashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        today = timezone.localdate()
        month_start = today.replace(day=1)
        today_orders = BookingOrder.objects.filter(created_at__date=today).count()
        today_checkins = BookingOrder.objects.filter(check_in_date=today).count()
        today_checkouts = BookingOrder.objects.filter(check_out_date=today).count()
        today_revenue = BookingOrder.objects.filter(created_at__date=today, payment_status=BookingOrder.PAYMENT_PAID).aggregate(total=Sum("pay_amount"))["total"] or Decimal("0.00")
        month_revenue = BookingOrder.objects.filter(created_at__date__gte=month_start, payment_status=BookingOrder.PAYMENT_PAID).aggregate(total=Sum("pay_amount"))["total"] or Decimal("0.00")
        total_rooms = RoomType.objects.aggregate(total=Sum("stock"))["total"] or 0
        occupied = BookingOrder.objects.filter(status=BookingOrder.STATUS_CHECKED_IN).count()
        occupancy_rate = round((occupied / total_rooms) * 100, 2) if total_rooms else 0
        return api_response(
            data={
                "today_order_count": today_orders,
                "today_check_in_count": today_checkins,
                "today_check_out_count": today_checkouts,
                "today_revenue": today_revenue,
                "month_revenue": month_revenue,
                "occupancy_rate": occupancy_rate,
                "pending_review_count": Review.objects.filter(reply_content="").count(),
                "pending_report_task_count": ReportTask.objects.filter(status=ReportTask.STATUS_PENDING).count(),
            }
        )


class AdminDashboardChartsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        end_date = parse_date(request.query_params.get("end_date", "")) or timezone.localdate()
        start_date = parse_date(request.query_params.get("start_date", "")) or (end_date - timedelta(days=6))
        items = []
        current = start_date
        while current <= end_date:
            day_orders = BookingOrder.objects.filter(created_at__date=current).count()
            day_revenue = BookingOrder.objects.filter(created_at__date=current, payment_status=BookingOrder.PAYMENT_PAID).aggregate(total=Sum("pay_amount"))["total"] or Decimal("0.00")
            items.append(
                {
                    "date": current.strftime("%Y-%m-%d"),
                    "order_count": day_orders,
                    "revenue": float(day_revenue),
                }
            )
            current += timedelta(days=1)
        return api_response(data={"items": items})


class AdminHotelsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = Hotel.objects.all()
        keyword = request.query_params.get("keyword")
        status = request.query_params.get("status")
        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(address__icontains=keyword))
        if status:
            queryset = queryset.filter(status=status)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=HotelSimpleSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)

    def post(self, request):
        if request.path.endswith("/create"):
            serializer = HotelCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
            hotel = serializer.save()
            return api_response(data=HotelSimpleSerializer(hotel).data)
        if request.path.endswith("/update"):
            serializer = HotelUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
            hotel = Hotel.objects.filter(pk=serializer.validated_data["hotel_id"]).first()
            if not hotel:
                return api_response(code=4040, message="酒店不存在", data=None, status_code=404)
            for field, value in serializer.validated_data.items():
                if field != "hotel_id":
                    setattr(hotel, field, value)
            hotel.save()
            return api_response(data=HotelSimpleSerializer(hotel).data)
        hotel_id = request.data.get("hotel_id")
        deleted, _ = Hotel.objects.filter(pk=hotel_id).delete()
        if not deleted:
            return api_response(code=4040, message="酒店不存在", data=None, status_code=404)
        return api_response(data={"hotel_id": hotel_id, "deleted": True})


class AdminRoomTypesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = RoomType.objects.select_related("hotel")
        hotel_id = request.query_params.get("hotel_id")
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=RoomTypeSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)

    def post(self, request):
        if request.path.endswith("/create"):
            serializer = RoomTypeCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
            room_type = serializer.save()
            return api_response(data=RoomTypeSerializer(room_type).data)
        if request.path.endswith("/update"):
            serializer = RoomTypeUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
            room_type = RoomType.objects.filter(pk=serializer.validated_data["room_type_id"]).first()
            if not room_type:
                return api_response(code=4040, message="房型不存在", data=None, status_code=404)
            for field, value in serializer.validated_data.items():
                if field != "room_type_id":
                    setattr(room_type, field, value)
            room_type.save()
            return api_response(data=RoomTypeSerializer(room_type).data)
        room_type_id = request.data.get("room_type_id")
        deleted, _ = RoomType.objects.filter(pk=room_type_id).delete()
        if not deleted:
            return api_response(code=4040, message="房型不存在", data=None, status_code=404)
        return api_response(data={"room_type_id": room_type_id, "deleted": True})


class AdminInventoryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        room_type_id = request.query_params.get("room_type_id")
        start_date = parse_date(request.query_params.get("start_date", ""))
        end_date = parse_date(request.query_params.get("end_date", ""))
        queryset = RoomInventory.objects.all()
        if room_type_id:
            queryset = queryset.filter(room_type_id=room_type_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        queryset = queryset.order_by("date", "room_type_id")
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=RoomInventorySerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)

    def post(self, request):
        serializer = InventoryUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        inventory, _ = RoomInventory.objects.update_or_create(
            room_type_id=data["room_type_id"],
            date=data["date"],
            defaults={
                "price": data["price"],
                "stock": data["stock"],
                "status": data["status"],
            },
        )
        return api_response(data=RoomInventorySerializer(inventory).data)


class AdminOrdersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = BookingOrder.objects.select_related("hotel", "room_type", "user")
        keyword = request.query_params.get("keyword")
        status = request.query_params.get("status")
        if keyword:
            queryset = queryset.filter(
                Q(order_no__icontains=keyword)
                | Q(guest_mobile__icontains=keyword)
                | Q(guest_name__icontains=keyword)
            )
        if status:
            queryset = queryset.filter(status=status)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=BookingOrderSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)


class AdminOrdersDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        order_id = request.query_params.get("order_id")
        order = BookingOrder.objects.filter(id=order_id).select_related("hotel", "room_type").first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        return api_response(data=BookingOrderSerializer(order).data)


class AdminOrdersChangeStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = OrderStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        order = BookingOrder.objects.filter(id=serializer.validated_data["order_id"]).first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        order.status = serializer.validated_data["target_status"]
        order.save(update_fields=["status", "updated_at"])
        return api_response(data={"order_id": order.id, "status": order.status})


class AdminOrdersCheckInView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = CheckInSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"]).first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        order.status = BookingOrder.STATUS_CHECKED_IN
        order.room_no = data["room_no"]
        order.operator_remark = data.get("operator_remark", "")
        order.save(update_fields=["status", "room_no", "operator_remark", "updated_at"])
        return api_response(data={"order_id": order.id, "status": order.status, "room_no": order.room_no})


class AdminOrdersCheckOutView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = CheckOutSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"]).first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        order.status = BookingOrder.STATUS_COMPLETED
        order.operator_remark = data.get("operator_remark", "")
        order.save(update_fields=["status", "operator_remark", "updated_at"])
        return api_response(data={"order_id": order.id, "status": order.status})


class AdminReviewsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = Review.objects.select_related("user", "hotel")
        hotel_id = request.query_params.get("hotel_id")
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=ReviewSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)


class AdminReviewsReplyView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = ReplyReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        review = Review.objects.filter(id=serializer.validated_data["review_id"]).first()
        if not review:
            return api_response(code=4040, message="评价不存在", data=None, status_code=404)
        review.reply_content = serializer.validated_data["content"]
        review.save(update_fields=["reply_content", "updated_at"])
        return api_response(data={"review_id": review.id, "reply_content": review.reply_content})


class AdminUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = UserProfile.objects.select_related("user")
        keyword = request.query_params.get("keyword")
        if keyword:
            queryset = queryset.filter(Q(user__username__icontains=keyword) | Q(mobile__icontains=keyword) | Q(nickname__icontains=keyword))
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=UserProfileSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)


class AdminUsersChangeStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = ChangeUserStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        profile = UserProfile.objects.filter(user_id=serializer.validated_data["user_id"]).first()
        if not profile:
            return api_response(code=4040, message="用户不存在", data=None, status_code=404)
        profile.status = serializer.validated_data["status"]
        profile.save(update_fields=["status", "updated_at"])
        return api_response(data={"user_id": profile.user_id, "status": profile.status})


class AdminEmployeesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = UserProfile.objects.select_related("user").filter(role__in=[UserProfile.ROLE_HOTEL_ADMIN, UserProfile.ROLE_SYSTEM_ADMIN])
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=UserProfileSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)

    def post(self, request):
        serializer = EmployeeCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        if User.objects.filter(username=data["username"]).exists():
            return api_response(code=4090, message="用户名已存在", data=None, status_code=409)
        user = User.objects.create_user(username=data["username"], password=data["password"])
        profile = UserProfile.objects.create(
            user=user,
            nickname=data["name"],
            mobile=data["mobile"],
            role=data["role"],
            status=UserProfile.STATUS_ACTIVE,
        )
        return api_response(data=UserProfileSerializer(profile).data)


class AdminSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        return api_response(
            data={
                "platform_name": "HoteLink 酒店管理系统",
                "support_phone": "400-000-0000",
                "order_auto_cancel_minutes": 30,
            }
        )

    def post(self, request):
        serializer = SettingsUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        return api_response(data=serializer.validated_data)


class AdminAISettingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        ai_settings = settings.AI_SETTINGS
        return api_response(
            data={
                "provider": ai_settings.provider,
                "ai_enabled": ai_settings.enabled,
                "chat_model": ai_settings.chat_model,
                "reasoning_model": ai_settings.reasoning_model,
                "base_url": ai_settings.base_url,
                "api_key_configured": ai_settings.is_configured,
            }
        )

    def post(self, request):
        serializer = AISettingsUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        return api_response(data=serializer.validated_data)


class AdminAIReportSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AIReportSummarySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        orders = BookingOrder.objects.filter(check_in_date__gte=data["start_date"], check_out_date__lte=data["end_date"])
        if data.get("hotel_id"):
            orders = orders.filter(hotel_id=data["hotel_id"])
        total_orders = orders.count()
        total_revenue = orders.filter(payment_status=BookingOrder.PAYMENT_PAID).aggregate(total=Sum("pay_amount"))["total"] or Decimal("0.00")
        summary = f"统计区间内共有 {total_orders} 笔订单，已支付营收 {total_revenue} 元。建议结合取消率与房型均价进一步分析。"
        return api_response(data={"scene": "report_summary", "summary": summary})


class AdminAIReviewSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AIReviewSummarySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        reviews = Review.objects.filter(created_at__date__gte=data["start_date"], created_at__date__lte=data["end_date"])
        if data.get("hotel_id"):
            reviews = reviews.filter(hotel_id=data["hotel_id"])
        avg_score = reviews.aggregate(avg=Avg("score"))["avg"] or 0
        summary = f"统计区间内共有 {reviews.count()} 条评价，平均评分 {round(avg_score, 2)} 分。建议重点关注低分评价中的重复问题。"
        return api_response(data={"scene": "review_summary", "summary": summary})


class AdminAIReplySuggestionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AIReplySuggestionSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        review = Review.objects.filter(id=serializer.validated_data["review_id"]).first()
        if not review:
            return api_response(code=4040, message="评价不存在", data=None, status_code=404)
        suggestion = fallback_ai_reply("reply_suggestion")
        return api_response(data={"scene": "reply_suggestion", "suggested_reply": suggestion})


class AdminReportTasksView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = ReportTask.objects.select_related("hotel")
        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        items = []
        for task in page_queryset:
            items.append(
                {
                    "id": task.id,
                    "hotel_id": task.hotel_id,
                    "hotel_name": task.hotel.name if task.hotel_id else "",
                    "report_type": task.report_type,
                    "start_date": task.start_date,
                    "end_date": task.end_date,
                    "status": task.status,
                    "result_summary": task.result_summary,
                    "created_at": task.created_at,
                }
            )
        return paginated_response(items=items, page=page, page_size=page_size, total=total)

    def post(self, request):
        serializer = ReportTaskCreateSimpleSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="invalid parameters", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        task = ReportTask.objects.create(
            hotel_id=data.get("hotel_id"),
            report_type=data["report_type"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            status=ReportTask.STATUS_SUCCESS,
            result_summary="已生成示例报表，可在后续接入异步任务后扩展为真实报表。",
        )
        return api_response(
            data={
                "id": task.id,
                "report_type": task.report_type,
                "status": task.status,
                "result_summary": task.result_summary,
            }
        )
