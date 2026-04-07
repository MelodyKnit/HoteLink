"""
apps/api/views.py —— 项目所有 REST API 视图类。

按功能分为五组：
  《系统》  ApiRootView / SystemInitCheckView / SystemInitSetupView
  《认证》  UserRegisterView / BaseLoginView / UserLoginView / AdminLoginView /
            RefreshTokenApiView / LogoutApiView / UserAuthMeView
  《公共》  PublicHomeView / PublicHotelsView / PublicHotelSearchSuggestView /
            PublicHotelDetailView / PublicHotelReviewsView / PublicRoomTypeCalendarView /
            CommonCitiesView / CommonDictsView / CommonUploadView
  《用户》  UserProfileView / UserProfileAvatarView / UserPasswordChangeView /
            UserFavoritesView / UserOrdersView / UserOrdersDetailView /
            UserOrdersCreateView / UserOrdersUpdateView / UserOrdersPayView /
            UserOrdersCancelView / UserReviewsCreateView / UserPointsLogsView /
            UserNoticesView / UserCouponsView / UserInvoicesView /
            UserInvoiceTitleCreateView / UserInvoiceApplyView / UserAIChatView
  《管理员》  AdminDashboardOverviewView / AdminDashboardChartsView / AdminHotelsView /
            AdminRoomTypesView / AdminInventoryView / AdminOrdersView /
            AdminOrdersDetailView / AdminOrdersChangeStatusView /
            AdminOrdersCheckInView / AdminOrdersCheckOutView / AdminReviewsView /
            AdminReviewsReplyView / AdminUsersView / AdminUsersChangeStatusView /
            AdminEmployeesView / AdminSettingsView / AdminAISettingsView /
            AdminAIReportSummaryView / AdminAIReviewSummaryView /
            AdminAIReplySuggestionView / AdminReportTasksView
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import hashlib

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.db.models import Avg, Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.crypto import get_random_string
from PIL import Image, UnidentifiedImageError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.api.permissions import IsAdminRole
from apps.api.responses import api_response, paginated_response
from apps.api.serializers import (
    AIChatSerializer,
    AIProviderCreateSerializer,
    AIProviderDeleteSerializer,
    AIProviderSwitchSerializer,
    AIReplySuggestionSerializer,
    AIReportSummarySerializer,
    AIReviewSummarySerializer,
    AISettingsUpdateSerializer,
    BookingOrderSerializer,
    InitSetupSerializer,
    ChangeUserStatusSerializer,
    CheckInSerializer,
    CheckOutSerializer,
    ClaimCouponSerializer,
    CouponTemplateCreateSerializer,
    CouponTemplateSerializer,
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
    PointsLogSerializer,
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
    SystemResetSerializer,
    UploadSerializer,
    UserCouponSerializer,
    UserProfileSerializer,
)
from apps.bookings.models import BookingOrder
from apps.crm.models import CouponTemplate, FavoriteHotel, InvoiceRequest, InvoiceTitle, PointsLog, Review, UserCoupon
from apps.hotels.models import Hotel, RoomInventory, RoomType
from apps.operations.models import SystemNotice
from apps.operations.services.ai_service import AIChatService
from apps.operations.services.prompt_service import PromptSceneError
from config.ai import load_ai_settings, update_ai_settings, BUILTIN_PROVIDERS
from apps.payments.models import PaymentRecord
from apps.reports.models import ReportTask
from apps.users.models import UserProfile

User = get_user_model()


def ensure_profile(user: User) -> UserProfile:
    """
    确保用户存在对应的 UserProfile。
    若不存在则自动创建，超级用户默认为 system_admin。
    """
    defaults = {
        "nickname": user.username,
        "mobile": "",
        "role": UserProfile.ROLE_SYSTEM_ADMIN if user.is_superuser else UserProfile.ROLE_USER,
        "status": UserProfile.STATUS_ACTIVE,
    }
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults=defaults)
    return profile


def add_points(user, points: int, log_type: str, description: str, order=None):
    """给用户增加积分并记录日志，自动触发会员升级。"""
    if points == 0:
        return
    profile = ensure_profile(user)
    profile.points = max(0, profile.points + points)
    profile.save(update_fields=["points", "updated_at"])
    PointsLog.objects.create(
        user=user,
        log_type=log_type,
        points=points,
        balance=profile.points,
        description=description,
        order=order,
    )
    old_level = profile.member_level
    if profile.refresh_level() and old_level != profile.member_level:
        level_name = dict(UserProfile.MEMBER_LEVEL_CHOICES).get(profile.member_level, profile.member_level)
        SystemNotice.objects.create(
            user=user,
            notice_type=SystemNotice.TYPE_MEMBER,
            title="会员升级啦！",
            content=f"恭喜您升级为{level_name}，享受更多专属权益！",
        )


def get_page_params(request) -> tuple[int, int]:
    """
    从查询参数中解析 page 和 page_size。
    page 最小为 1，page_size 限制在 [1, 100] 之间。
    """
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
    """
    对 queryset 进行内存分页切片。

    Returns:
        (page_queryset, total) 元组：当前页数据切片和总记录数。
    """
    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    return queryset[start:end], total


def parse_thumb_params(request) -> tuple[int, int]:
    try:
        width = int(request.query_params.get("w", 56))
    except (TypeError, ValueError):
        width = 56
    try:
        height = int(request.query_params.get("h", 40))
    except (TypeError, ValueError):
        height = 40
    return min(max(width, 16), 512), min(max(height, 16), 512)


def get_thumb_size_by_mode(mode: str | None) -> tuple[int, int]:
    if mode == "compact":
        return 48, 32
    if mode == "standard":
        return 56, 40
    return 56, 40


def mask_mobile(mobile: str) -> str:
    value = (mobile or "").strip()
    if len(value) < 7:
        return value
    return f"{value[:3]}***{value[-3:]}"


def build_tokens_for_user(user: User) -> dict:
    """
    为指定用户生成 JWT Access / Refresh Token 对。

    Returns:
        包含 access_token、refresh_token、token_type、expires_in 的字典。
    """
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "token_type": "Bearer",
        "expires_in": 60 * 60 * 2,
    }


def make_order_no() -> str:
    """生成唯一订单号，格式：HT + 时间戳(14位) + 4位随机数字。"""
    now = timezone.localtime()
    return f"HT{now.strftime('%Y%m%d%H%M%S')}{get_random_string(4, allowed_chars='0123456789')}"


def make_payment_no() -> str:
    """生成唯一支付流水号，格式：PM + 时间戳(14位) + 4位随机数字。"""
    now = timezone.localtime()
    return f"PM{now.strftime('%Y%m%d%H%M%S')}{get_random_string(4, allowed_chars='0123456789')}"


def fallback_ai_reply(scene: str) -> str:
    """
    当 AI 服务未配置或调用失败时返回占位回复文本。

    Args:
        scene: AI 场景标识：customer_service / report_summary / review_summary / reply_suggestion。
    """
    if scene == "customer_service":
        return "您好，这里是 HoteLink 智能客服。当前我暂时无法从系统已接入的数据中生成可靠答复，请稍后重试，或联系人工客服进一步处理。"
    if scene == "report_summary":
        return "当前时间段内营收与订单波动建议结合入住率、取消率和均价变化综合判断。"
    if scene == "review_summary":
        return "近期评价主要关注服务体验、卫生情况和入住便利性，建议优先处理重复出现的问题。"
    if scene == "reply_suggestion":
        return "感谢您的反馈，我们会认真优化相关体验，期待您的再次入住。"
    return f"当前为 {scene} 场景的占位回复。"


def get_dict_payload() -> dict:
    """返回系统内置字典数据，包括酒店星级、支付方式、床型等列举选项。"""
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
    """API 根入口，返回版本和用户端/管理端基准路径。"""
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
    """用户注册接口：创建 Django 用户并初始化 UserProfile。"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)

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


class SystemInitCheckView(APIView):
    """系统初始化状态检查：判断是否已存在管理员账号。"""
    """检查系统是否已完成初始化（是否存在管理员账号）"""
    permission_classes = [AllowAny]

    def get(self, request):
        has_admin = UserProfile.objects.filter(
            role__in=[UserProfile.ROLE_SYSTEM_ADMIN, UserProfile.ROLE_HOTEL_ADMIN]
        ).exists()
        return api_response(data={"initialized": has_admin})


class SystemInitSetupView(APIView):
    """系统首次初始化：创建首个系统管理员并返回登录令牌。"""
    """首次初始化：创建管理员账号（仅当系统中无管理员时可用）"""
    permission_classes = [AllowAny]

    def post(self, request):
        has_admin = UserProfile.objects.filter(
            role__in=[UserProfile.ROLE_SYSTEM_ADMIN, UserProfile.ROLE_HOTEL_ADMIN]
        ).exists()
        if has_admin:
            return api_response(code=4030, message="系统已初始化，无法重复创建", data=None, status_code=403)

        serializer = InitSetupSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)

        data = serializer.validated_data
        if User.objects.filter(username=data["username"]).exists():
            return api_response(code=4090, message="用户名已存在", data=None, status_code=409)

        user = User.objects.create_user(username=data["username"], password=data["password"])
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        UserProfile.objects.create(
            user=user,
            nickname=data["username"],
            mobile="",
            role=UserProfile.ROLE_SYSTEM_ADMIN,
            status=UserProfile.STATUS_ACTIVE,
        )

        tokens = build_tokens_for_user(user)
        return api_response(data={
            **tokens,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": UserProfile.ROLE_SYSTEM_ADMIN,
            },
        })


class BaseLoginView(APIView):
    """通用登录基类：完成用户名密码校验、角色限制和 JWT 发放。"""
    permission_classes = [AllowAny]
    required_roles: set[str] | None = None

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)

        user = authenticate(
            request=request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return api_response(code=4010, message="用户名或密码错误", data=None, status_code=401)

        profile = ensure_profile(user)
        if self.required_roles and profile.role not in self.required_roles and not user.is_superuser:
            return api_response(code=4030, message="权限不足", data=None, status_code=403)

        tokens = build_tokens_for_user(user)
        return api_response(
            data={
                **tokens,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": profile.role,
                    "nickname": profile.nickname,
                    "member_level": profile.member_level,
                    "avatar": profile.avatar,
                    "points": profile.points,
                },
            }
        )


class UserLoginView(BaseLoginView):
    """前台用户登录入口，允许 user/hotel_admin/system_admin。"""
    required_roles = {"user", "hotel_admin", "system_admin"}


class AdminLoginView(BaseLoginView):
    """管理端登录入口，仅允许 hotel_admin/system_admin。"""
    required_roles = {"hotel_admin", "system_admin"}


class RefreshTokenApiView(APIView):
    """刷新 Access Token 接口：使用 refresh_token 续期登录态。"""
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
    """退出登录接口（无状态 JWT 场景下返回前端确认结果）。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return api_response(data={"logged_out": True})


class UserAuthMeView(APIView):
    """当前登录用户信息接口。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ensure_profile(request.user)
        return api_response(data=UserProfileSerializer(profile).data)


class CommonCitiesView(APIView):
    """公共城市列表接口：返回酒店库中可选城市。"""
    permission_classes = [AllowAny]

    def get(self, request):
        cities = list(Hotel.objects.exclude(city="").values_list("city", flat=True).distinct().order_by("city"))
        return api_response(data={"items": [{"label": city, "value": city} for city in cities]})


class CommonDictsView(APIView):
    """公共字典接口：返回星级、支付方式、床型等静态枚举。"""
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
    """通用文件上传接口：按业务场景保存文件并返回可访问 URL。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        file_obj = serializer.validated_data["file"]
        scene = serializer.validated_data["scene"]
        path = default_storage.save(f"uploads/{scene}/{file_obj.name}", file_obj)
        file_url = request.build_absolute_uri(f"/media/{path}")
        return api_response(data={"file_name": file_obj.name, "file_url": file_url, "scene": scene})


class CommonImageThumbView(APIView):
    """图片缩略图接口：将 /media 下图片按指定尺寸缩放并缓存后返回。"""
    permission_classes = [AllowAny]

    def get(self, request):
        url = request.query_params.get("url", "")
        width, height = parse_thumb_params(request)
        if not url:
            return api_response(code=4001, message="缺少图片URL", data=None, status_code=400)
        if not str(url).startswith(settings.MEDIA_URL):
            return api_response(code=4001, message="仅支持站内媒体URL", data=None, status_code=400)

        rel_path = str(url)[len(settings.MEDIA_URL):].lstrip("/")
        media_root = Path(settings.MEDIA_ROOT).resolve()
        source_path = (media_root / rel_path).resolve()
        if not str(source_path).startswith(str(media_root)):
            return api_response(code=4001, message="无效的媒体路径", data=None, status_code=400)
        if not source_path.exists() or not source_path.is_file():
            return api_response(code=4040, message="image not found", data=None, status_code=404)

        cache_root = media_root / ".thumb_cache"
        cache_root.mkdir(parents=True, exist_ok=True)
        cache_key = hashlib.md5(f"{source_path}:{source_path.stat().st_mtime_ns}:{width}x{height}".encode("utf-8")).hexdigest()
        cache_path = cache_root / f"{cache_key}.jpg"

        if cache_path.exists():
            content = cache_path.read_bytes()
            resp = HttpResponse(content, content_type="image/jpeg")
            resp["Cache-Control"] = "public, max-age=604800, immutable"
            return resp

        try:
            with Image.open(source_path) as img:
                img = img.convert("RGB")
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                buf = BytesIO()
                img.save(buf, format="JPEG", quality=72, optimize=True)
                content = buf.getvalue()
        except (UnidentifiedImageError, OSError):
            return api_response(code=4001, message="invalid image", data=None, status_code=400)

        cache_path.write_bytes(content)
        resp = HttpResponse(content, content_type="image/jpeg")
        resp["Cache-Control"] = "public, max-age=604800, immutable"
        return resp


class PublicHomeView(APIView):
    """首页聚合接口：返回推荐酒店、推荐房型和活动信息。"""
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
    """酒店列表检索接口：支持关键字、城市、价格、星级和排序分页。"""
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
    """酒店搜索建议接口：按关键字返回简要联想候选。"""
    permission_classes = [AllowAny]

    def get(self, request):
        keyword = request.query_params.get("keyword", "").strip()
        if not keyword:
            return api_response(data={"items": []})
        hotels = Hotel.objects.filter(status=Hotel.STATUS_ONLINE, name__icontains=keyword).order_by("-is_recommended", "name")[:10]
        items = [{"hotel_id": hotel.id, "name": hotel.name, "city": hotel.city} for hotel in hotels]
        return api_response(data={"items": items})


class PublicHotelDetailView(APIView):
    """酒店详情接口：返回酒店信息及房型明细。"""
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
    """酒店评价列表接口：支持评分筛选和分页。"""
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
    """房型日历库存接口：查询区间库存，不存在时按默认库存回填。"""
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
    """用户资料接口：查询和更新昵称/手机号/性别/生日/邮箱。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return api_response(data=UserProfileSerializer(ensure_profile(request.user)).data)

    def post(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
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
    """用户头像上传接口。"""
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
    """用户修改密码接口，需校验旧密码。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        if not request.user.check_password(data["old_password"]):
            return api_response(code=4001, message="旧密码不正确", data=None, status_code=400)
        request.user.set_password(data["new_password"])
        request.user.save()
        return api_response(data={"changed": True})


class UserFavoritesView(APIView):
    """用户收藏接口：查询收藏列表并支持新增/取消收藏。"""
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
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        hotel = Hotel.objects.filter(pk=serializer.validated_data["hotel_id"]).first()
        if not hotel:
            return api_response(code=4040, message="酒店不存在", data=None, status_code=404)

        if request.path.endswith("/add"):
            favorite, _ = FavoriteHotel.objects.get_or_create(user=request.user, hotel=hotel)
            return api_response(data={"favorite_id": favorite.id, "hotel_id": hotel.id})
        FavoriteHotel.objects.filter(user=request.user, hotel=hotel).delete()
        return api_response(data={"hotel_id": hotel.id, "removed": True})


class UserOrdersView(APIView):
    """用户订单列表接口：按状态筛选并分页返回。"""
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


class UserOrderGuestHistoryView(APIView):
    """用户历史入住人信息接口：返回最近常用入住人，供下单自动填充。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 6))
        except (TypeError, ValueError):
            limit = 6
        limit = min(max(limit, 1), 20)

        queryset = (
            BookingOrder.objects.filter(user=request.user)
            .exclude(guest_name="")
            .exclude(guest_mobile="")
            .order_by("-created_at")
            .values("guest_name", "guest_mobile")
        )

        seen: set[tuple[str, str]] = set()
        items = []
        for row in queryset:
            name = str(row.get("guest_name") or "").strip()
            mobile = str(row.get("guest_mobile") or "").strip()
            if not name or not mobile:
                continue
            key = (name, mobile)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                {
                    "guest_name": name,
                    "guest_mobile": mobile,
                    "masked_mobile": mask_mobile(mobile),
                }
            )
            if len(items) >= limit:
                break
        return api_response(data={"items": items})


class UserOrdersDetailView(APIView):
    """用户订单详情接口，仅允许查看自己的订单。"""
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
    """创建订单接口：校验房型与日期后生成订单，应用会员折扣与优惠券。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)

        data = serializer.validated_data
        hotel = Hotel.objects.filter(pk=data["hotel_id"]).first()
        room_type = RoomType.objects.filter(pk=data["room_type_id"], hotel_id=data["hotel_id"]).first()
        if not hotel or not room_type:
            return api_response(code=4040, message="酒店或房型不存在", data=None, status_code=404)

        nights = (data["check_out_date"] - data["check_in_date"]).days
        if nights <= 0:
            return api_response(code=4001, message="离店日期必须大于入住日期", data=None, status_code=400)
        original_amount = room_type.base_price * nights

        # 1. 会员折扣
        profile = ensure_profile(request.user)
        member_discount_rate = Decimal(str(profile.discount_rate))
        member_discounted = (original_amount * member_discount_rate).quantize(Decimal("0.01"))
        member_discount_amount = original_amount - member_discounted

        # 2. 优惠券
        coupon_discount_amount = Decimal("0.00")
        coupon_obj = None
        coupon_id = data.get("coupon_id")
        if coupon_id:
            from django.utils import timezone as tz
            today = tz.localdate()
            coupon_obj = UserCoupon.objects.filter(
                id=coupon_id, user=request.user, status=UserCoupon.STATUS_UNUSED,
                valid_start__lte=today, valid_end__gte=today,
            ).first()
            if not coupon_obj:
                return api_response(code=4001, message="优惠券不可用", data=None, status_code=400)
            if coupon_obj.min_amount and member_discounted < coupon_obj.min_amount:
                return api_response(code=4001, message=f"未满足优惠券最低消费 ¥{coupon_obj.min_amount}", data=None, status_code=400)
            if coupon_obj.coupon_type == UserCoupon.TYPE_CASH:
                coupon_discount_amount = min(coupon_obj.amount, member_discounted)
            elif coupon_obj.coupon_type == UserCoupon.TYPE_DISCOUNT:
                coupon_discount_amount = (member_discounted * (Decimal("1") - coupon_obj.discount / Decimal("10"))).quantize(Decimal("0.01"))

        total_discount = member_discount_amount + coupon_discount_amount
        pay_amount = max(original_amount - total_discount, Decimal("0.00"))

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
            member_discount_amount=member_discount_amount,
            coupon_discount_amount=coupon_discount_amount,
            discount_amount=total_discount,
            pay_amount=pay_amount,
            coupon=coupon_obj,
        )

        # 核销优惠券
        if coupon_obj:
            coupon_obj.status = UserCoupon.STATUS_USED
            coupon_obj.used_order = order
            coupon_obj.used_at = timezone.now()
            coupon_obj.save(update_fields=["status", "used_order", "used_at"])

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
                "member_discount_amount": order.member_discount_amount,
                "coupon_discount_amount": order.coupon_discount_amount,
                "discount_amount": order.discount_amount,
                "pay_amount": order.pay_amount,
            }
        )


class UserOrdersUpdateView(APIView):
    """用户订单更新接口：修改联系人姓名/手机号/备注。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
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
    """用户订单支付接口：创建支付记录并更新订单支付状态。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderPaySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
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

        # 支付成功后奖励积分：每消费10元=1积分 × 会员倍率
        profile = ensure_profile(request.user)
        base_points = int(order.pay_amount / Decimal("10"))
        earned_points = max(1, int(base_points * Decimal(str(profile.points_multiplier))))
        if earned_points > 0:
            order.points_earned = earned_points
            order.save(update_fields=["points_earned"])
            add_points(
                request.user, earned_points, PointsLog.TYPE_CONSUME_REWARD,
                f"订单 {order.order_no} 消费奖励（{profile.points_multiplier}x倍率）",
                order=order,
            )

        SystemNotice.objects.create(
            user=request.user,
            notice_type=SystemNotice.TYPE_PAYMENT,
            title="支付成功",
            content=f"订单 {order.order_no} 已完成支付。",
        )
        return api_response(data={"order_id": order.id, "payment_id": payment.id, "payment_status": order.payment_status})


class UserOrdersCancelView(APIView):
    """用户取消订单接口：限制已入住/已完成/已取消订单不可取消。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCancelSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
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
    """用户评价创建接口：可新增或更新评价，首评奖励积分。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
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
            add_points(request.user, 10, PointsLog.TYPE_REVIEW_REWARD, f"评价订单 {order.order_no} 奖励", order=order)
        return api_response(data={"review_id": review.id, "score": review.score})


class UserPointsLogsView(APIView):
    """用户积分日志接口：返回真实积分变动记录。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ensure_profile(request.user)
        queryset = PointsLog.objects.filter(user=request.user)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return api_response(data={
            "current_points": profile.points,
            "member_level": profile.member_level,
            "items": PointsLogSerializer(page_queryset, many=True).data,
            "total": total,
        })


class UserNoticesView(APIView):
    """用户站内通知列表接口，支持标记已读。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page, page_size = get_page_params(request)
        queryset = SystemNotice.objects.filter(user=request.user)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        unread_count = SystemNotice.objects.filter(user=request.user, is_read=False).count()
        return paginated_response(
            items=SystemNoticeSerializer(page_queryset, many=True).data,
            page=page,
            page_size=page_size,
            total=total,
            extra={"unread_count": unread_count},
        )

    def post(self, request):
        """标记通知已读：ids=[] 标记指定，ids=null/不传 标记全部已读。"""
        ids = request.data.get("ids")
        queryset = SystemNotice.objects.filter(user=request.user, is_read=False)
        if ids:
            queryset = queryset.filter(id__in=ids)
        queryset.update(is_read=True)
        unread_count = SystemNotice.objects.filter(user=request.user, is_read=False).count()
        return api_response(data={"unread_count": unread_count})

    def delete(self, request):
        """删除通知：ids=[1,2,3] 删除指定，不传 ids 则删除全部。"""
        ids = request.data.get("ids")
        queryset = SystemNotice.objects.filter(user=request.user)
        if ids:
            queryset = queryset.filter(id__in=ids)
        deleted_count, _ = queryset.delete()
        unread_count = SystemNotice.objects.filter(user=request.user, is_read=False).count()
        return api_response(data={"deleted": deleted_count, "unread_count": unread_count})


class UserNoticeUnreadCountView(APIView):
    """用户未读通知数量接口。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = SystemNotice.objects.filter(user=request.user, is_read=False).count()
        return api_response(data={"unread_count": count})


class UserCouponsView(APIView):
    """用户优惠券列表接口，支持 status 筛选。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = UserCoupon.objects.filter(user=request.user)
        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=UserCouponSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)


class UserAvailableCouponsView(APIView):
    """可领取的优惠券模板列表。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        profile = ensure_profile(request.user)
        queryset = CouponTemplate.objects.filter(
            status=CouponTemplate.STATUS_ACTIVE,
            valid_start__lte=today, valid_end__gte=today,
        )
        result = []
        for tpl in queryset:
            if tpl.remaining <= 0:
                continue
            if tpl.required_level:
                thresholds = UserProfile.MEMBER_THRESHOLDS
                user_threshold = thresholds.get(profile.member_level, 0)
                required_threshold = thresholds.get(tpl.required_level, 0)
                if user_threshold < required_threshold:
                    continue
            claimed = UserCoupon.objects.filter(user=request.user, template=tpl).count()
            if claimed >= tpl.per_user_limit:
                continue
            result.append({
                **CouponTemplateSerializer(tpl).data,
                "already_claimed": claimed,
            })
        return api_response(data={"items": result})


class UserClaimCouponView(APIView):
    """用户领取优惠券接口（免费或积分兑换）。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClaimCouponSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        tpl = CouponTemplate.objects.filter(id=serializer.validated_data["template_id"]).first()
        if not tpl:
            return api_response(code=4040, message="优惠券不存在", data=None, status_code=404)
        today = timezone.localdate()
        if tpl.status != CouponTemplate.STATUS_ACTIVE or today < tpl.valid_start or today > tpl.valid_end:
            return api_response(code=4001, message="优惠券活动已结束", data=None, status_code=400)
        if tpl.remaining <= 0:
            return api_response(code=4001, message="优惠券已领完", data=None, status_code=400)
        profile = ensure_profile(request.user)
        if tpl.required_level:
            thresholds = UserProfile.MEMBER_THRESHOLDS
            if thresholds.get(profile.member_level, 0) < thresholds.get(tpl.required_level, 0):
                level_name = dict(UserProfile.MEMBER_LEVEL_CHOICES).get(tpl.required_level, tpl.required_level)
                return api_response(code=4001, message=f"需要达到{level_name}才能领取", data=None, status_code=400)
        claimed = UserCoupon.objects.filter(user=request.user, template=tpl).count()
        if claimed >= tpl.per_user_limit:
            return api_response(code=4001, message="已达领取上限", data=None, status_code=400)
        if tpl.points_cost > 0:
            if profile.points < tpl.points_cost:
                return api_response(code=4001, message=f"积分不足，需要 {tpl.points_cost} 积分", data=None, status_code=400)
            add_points(request.user, -tpl.points_cost, PointsLog.TYPE_COUPON_EXCHANGE, f"兑换优惠券「{tpl.name}」")

        valid_start = today
        valid_end = today + timedelta(days=tpl.valid_days)
        if valid_end > tpl.valid_end:
            valid_end = tpl.valid_end
        coupon = UserCoupon.objects.create(
            user=request.user,
            template=tpl,
            name=tpl.name,
            coupon_type=tpl.coupon_type,
            amount=tpl.amount,
            discount=tpl.discount,
            min_amount=tpl.min_amount,
            valid_start=valid_start,
            valid_end=valid_end,
        )
        tpl.claimed_count += 1
        tpl.save(update_fields=["claimed_count", "updated_at"])
        coupon_type_name = "折扣券" if tpl.coupon_type == CouponTemplate.TYPE_DISCOUNT else "满减券"
        SystemNotice.objects.create(
            user=request.user,
            notice_type=SystemNotice.TYPE_COUPON,
            title=f"优惠券已到账",
            content=f"您已成功领取「{tpl.name}」{coupon_type_name}，有效期至 {valid_end.strftime('%Y-%m-%d')}，快去使用吧！",
        )
        return api_response(data=UserCouponSerializer(coupon).data)


class UserOrderAvailableCouponsView(APIView):
    """下单时查询可用优惠券列表。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        try:
            order_amount = Decimal(request.query_params.get("amount", "0"))
        except Exception:
            order_amount = Decimal("0")
        queryset = UserCoupon.objects.filter(
            user=request.user, status=UserCoupon.STATUS_UNUSED,
            valid_start__lte=today, valid_end__gte=today,
        )
        result = []
        for c in queryset:
            if c.min_amount and order_amount < c.min_amount:
                continue
            result.append(UserCouponSerializer(c).data)
        return api_response(data={"items": result})


class UserInvoicesView(APIView):
    """用户发票申请记录列表接口。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = InvoiceRequest.objects.filter(invoice_title__user=request.user).select_related("invoice_title")
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=InvoiceRequestSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)


class UserInvoiceTitleCreateView(APIView):
    """用户新增发票抬头接口。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InvoiceTitleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        title = serializer.save(user=request.user)
        return api_response(data=InvoiceTitleSerializer(title).data)


class UserInvoiceApplyView(APIView):
    """用户申请开票接口：关联订单与发票抬头生成申请。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InvoiceApplySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"], user=request.user).first()
        title = InvoiceTitle.objects.filter(id=data["invoice_title_id"], user=request.user).first()
        if not order or not title:
            return api_response(code=4040, message="订单或发票抬头不存在", data=None, status_code=404)
        invoice_request = InvoiceRequest.objects.create(order=order, invoice_title=title)
        return api_response(data=InvoiceRequestSerializer(invoice_request).data)


class UserAIChatView(APIView):
    """用户 AI 客服接口：优先调用模型服务，失败时返回兜底文案。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AIChatSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        try:
            result = service.reply_customer_service(
                user=request.user,
                scene=data["scene"],
                question=data["question"],
                hotel_id=data.get("hotel_id"),
                order_id=data.get("order_id"),
                booking_context=data.get("booking_context"),
            )
        except PromptSceneError as exc:
            return api_response(code=4002, message=str(exc), data=None, status_code=400)

        answer = result["answer"] or fallback_ai_reply(result["scene"])
        return api_response(
            data={
                "answer": answer,
                "scene": result["scene"],
                "booking_assistant": result.get("booking_assistant"),
            }
        )


class UserAIChatStreamView(APIView):
    """用户 AI 客服流式接口：以 SSE 格式逐 token 推送回复内容。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import json
        from django.http import StreamingHttpResponse

        serializer = AIChatSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        try:
            result = service.reply_customer_service(
                user=request.user,
                scene=data["scene"],
                question=data["question"],
                hotel_id=data.get("hotel_id"),
                order_id=data.get("order_id"),
                booking_context=data.get("booking_context"),
            )
        except PromptSceneError as exc:
            return api_response(code=4002, message=str(exc), data=None, status_code=400)

        scene = result["scene"]
        booking_assistant = result.get("booking_assistant")

        def event_stream():
            try:
                if booking_assistant is not None:
                    yield f"data: {json.dumps({'type': 'meta', 'scene': scene, 'booking_assistant': booking_assistant}, ensure_ascii=False)}\n\n"
                    answer = result["answer"] or fallback_ai_reply(scene)
                    for chunk in service.iter_text_chunks(answer):
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'done': False}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'content': '', 'done': True}, ensure_ascii=False)}\n\n"
                    return

                if not service.is_available():
                    fallback = fallback_ai_reply(scene)
                    yield f"data: {json.dumps({'type': 'chunk', 'content': fallback, 'done': False}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'content': '', 'done': True})}\n\n"
                    return

                _, messages = service.build_customer_service_messages(
                    user=request.user,
                    scene=scene,
                    question=data["question"],
                    hotel_id=data.get("hotel_id"),
                    order_id=data.get("order_id"),
                )
                stream = service.stream_chat_completion(messages, temperature=0.2)
                for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    token = (delta.content or "") if delta else ""
                    done = (chunk.choices[0].finish_reason is not None) if chunk.choices else False
                    event_type = 'done' if done else 'chunk'
                    yield f"data: {json.dumps({'type': event_type, 'content': token, 'done': done}, ensure_ascii=False)}\n\n"
            except Exception:
                fallback = fallback_ai_reply(scene)
                yield f"data: {json.dumps({'type': 'chunk', 'content': fallback, 'done': False}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'content': '', 'done': True})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class AdminDashboardOverviewView(APIView):
    """管理端仪表盘总览接口：统计今日订单、营收、入住率等关键指标。"""
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
    """管理端图表数据接口：按日期区间聚合订单量与营收。"""
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
    """酒店管理接口：列表查询、创建、更新与删除。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    _HOTEL_ORDERING_WHITELIST = {"id", "-id", "name", "-name", "city", "-city", "star", "-star", "min_price", "-min_price"}

    def get(self, request):
        queryset = Hotel.objects.all()
        keyword = request.query_params.get("keyword")
        status = request.query_params.get("status")
        thumb_mode = request.query_params.get("thumb_mode")
        thumb_width, thumb_height = get_thumb_size_by_mode(thumb_mode)
        ordering = request.query_params.get("ordering", "-id")
        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(address__icontains=keyword))
        if status:
            queryset = queryset.filter(status=status)
        if ordering not in self._HOTEL_ORDERING_WHITELIST:
            ordering = "-id"
        queryset = queryset.order_by(ordering)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(
            items=HotelSimpleSerializer(
                page_queryset,
                many=True,
                context={"thumb_width": thumb_width, "thumb_height": thumb_height},
            ).data,
            page=page,
            page_size=page_size,
            total=total,
        )

    def post(self, request):
        if request.path.endswith("/create"):
            serializer = HotelCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
            hotel = serializer.save()
            return api_response(data=HotelSimpleSerializer(hotel).data)
        if request.path.endswith("/update"):
            serializer = HotelUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
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
    """房型管理接口：列表查询、创建、更新与删除。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    _ROOM_ORDERING_WHITELIST = {"id", "-id", "name", "-name", "base_price", "-base_price", "bed_type", "-bed_type"}

    def get(self, request):
        queryset = RoomType.objects.select_related("hotel")
        hotel_id = request.query_params.get("hotel_id")
        thumb_mode = request.query_params.get("thumb_mode")
        thumb_width, thumb_height = get_thumb_size_by_mode(thumb_mode)
        ordering = request.query_params.get("ordering", "-id")
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        if ordering not in self._ROOM_ORDERING_WHITELIST:
            ordering = "-id"
        queryset = queryset.order_by(ordering)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(
            items=RoomTypeSerializer(
                page_queryset,
                many=True,
                context={"thumb_width": thumb_width, "thumb_height": thumb_height},
            ).data,
            page=page,
            page_size=page_size,
            total=total,
        )

    def post(self, request):
        if request.path.endswith("/create"):
            serializer = RoomTypeCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
            room_type = serializer.save()
            return api_response(data=RoomTypeSerializer(room_type).data)
        if request.path.endswith("/update"):
            serializer = RoomTypeUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
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
    """库存日历管理接口：按日期和房型查询，并支持单日库存更新。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        room_type_id = request.query_params.get("room_type_id")
        start_date = parse_date(request.query_params.get("start_date", ""))
        end_date = parse_date(request.query_params.get("end_date", ""))
        if room_type_id and start_date and end_date and start_date <= end_date:
            existing = RoomInventory.objects.filter(
                room_type_id=room_type_id,
                date__gte=start_date,
                date__lte=end_date,
            ).exists()
            if not existing:
                room_type = RoomType.objects.filter(pk=room_type_id).first()
                if room_type:
                    to_create = []
                    current = start_date
                    while current <= end_date:
                        to_create.append(
                            RoomInventory(
                                room_type_id=room_type.id,
                                date=current,
                                price=room_type.base_price,
                                stock=room_type.stock,
                                status=RoomInventory.STATUS_AVAILABLE,
                            )
                        )
                        current += timedelta(days=1)
                    RoomInventory.objects.bulk_create(to_create, ignore_conflicts=True)
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
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
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
    """管理员订单列表接口：支持关键词与状态筛选。"""
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
    """管理员订单详情接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        order_id = request.query_params.get("order_id")
        order = BookingOrder.objects.filter(id=order_id).select_related("hotel", "room_type").first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        return api_response(data=BookingOrderSerializer(order).data)


class AdminOrdersChangeStatusView(APIView):
    """管理员订单状态流转接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = OrderStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        order = BookingOrder.objects.filter(id=serializer.validated_data["order_id"]).first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        target_status = serializer.validated_data["target_status"]
        order.status = target_status
        order.save(update_fields=["status", "updated_at"])
        # 发送订单状态变更通知
        _notice_map = {
            BookingOrder.STATUS_CONFIRMED: (
                "订单已确认",
                f"您的订单 {order.order_no} 已由酒店确认，请按时入住。",
            ),
            BookingOrder.STATUS_CANCELLED: (
                "订单已取消",
                f"您的订单 {order.order_no} 已被取消，如有疑问请联系客服。",
            ),
        }
        if target_status in _notice_map:
            title, content = _notice_map[target_status]
            SystemNotice.objects.create(
                user=order.user,
                notice_type=SystemNotice.TYPE_ORDER,
                title=title,
                content=content,
            )
        return api_response(data={"order_id": order.id, "status": order.status})


class AdminOrdersCheckInView(APIView):
    """入住办理接口：写入房号并切换订单状态为已入住。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = CheckInSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"]).select_related("user").first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        order.status = BookingOrder.STATUS_CHECKED_IN
        order.room_no = data["room_no"]
        order.operator_remark = data.get("operator_remark", "")
        order.save(update_fields=["status", "room_no", "operator_remark", "updated_at"])
        SystemNotice.objects.create(
            user=order.user,
            notice_type=SystemNotice.TYPE_ORDER,
            title="已确认入住",
            content=f"订单 {order.order_no} 已办理入住，您的房间号为 {order.room_no}，祝您入住愉快！",
        )
        return api_response(data={"order_id": order.id, "status": order.status, "room_no": order.room_no})


class AdminOrdersCheckOutView(APIView):
    """退房办理接口：切换订单状态为已完成。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = CheckOutSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"]).select_related("user").first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        order.status = BookingOrder.STATUS_COMPLETED
        order.operator_remark = data.get("operator_remark", "")
        order.save(update_fields=["status", "operator_remark", "updated_at"])
        SystemNotice.objects.create(
            user=order.user,
            notice_type=SystemNotice.TYPE_ORDER,
            title="退房完成",
            content=f"订单 {order.order_no} 已办理退房，感谢您的入住，期待再次欢迎您！",
        )
        # 退房完成后奖励积分
        add_points(order.user, 20, PointsLog.TYPE_CONSUME_REWARD, f"订单 {order.order_no} 入住奖励", order=order)
        return api_response(data={"order_id": order.id, "status": order.status})


class AdminReviewsView(APIView):
    """管理员评价列表接口。"""
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
    """管理员评价回复接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = ReplyReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        review = Review.objects.filter(id=serializer.validated_data["review_id"]).first()
        if not review:
            return api_response(code=4040, message="评价不存在", data=None, status_code=404)
        review.reply_content = serializer.validated_data["content"]
        review.save(update_fields=["reply_content", "updated_at"])
        return api_response(data={"review_id": review.id, "reply_content": review.reply_content})


class AdminUsersView(APIView):
    """管理员用户列表接口。"""
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
    """管理员用户状态修改接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = ChangeUserStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        profile = UserProfile.objects.filter(user_id=serializer.validated_data["user_id"]).first()
        if not profile:
            return api_response(code=4040, message="用户不存在", data=None, status_code=404)
        profile.status = serializer.validated_data["status"]
        profile.save(update_fields=["status", "updated_at"])
        return api_response(data={"user_id": profile.user_id, "status": profile.status})


class AdminEmployeesView(APIView):
    """管理员员工管理接口：查询员工列表并创建管理员账号。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = UserProfile.objects.select_related("user").filter(role__in=[UserProfile.ROLE_HOTEL_ADMIN, UserProfile.ROLE_SYSTEM_ADMIN])
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=UserProfileSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)

    def post(self, request):
        serializer = EmployeeCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
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
    """平台设置接口：读取与更新系统展示配置。"""
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
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        return api_response(data=serializer.validated_data)


class AdminAISettingsView(APIView):
    """AI 设置接口：查询当前 AI 多供应商配置，支持增删改查和切换活跃供应商。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        ai_settings = load_ai_settings()
        active = ai_settings.get_active_provider()
        return api_response(
            data={
                "ai_enabled": ai_settings.enabled,
                "active_provider": ai_settings.active_provider,
                "providers": ai_settings.list_providers(),
                "builtin_providers": list(BUILTIN_PROVIDERS.keys()),
                "current_provider": active.to_dict() if active else None,
            }
        )

    def post(self, request):
        serializer = AISettingsUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        new_settings = update_ai_settings(
            enabled=data.get("ai_enabled"),
            active_provider=data.get("active_provider"),
            provider_configs=data.get("providers"),
        )
        return api_response(data={
            "ai_enabled": new_settings.enabled,
            "active_provider": new_settings.active_provider,
            "providers": new_settings.list_providers(),
        })


class AdminAIProviderAddView(APIView):
    """新增或编辑 AI 供应商接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AIProviderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        new_settings = update_ai_settings(provider_configs=[data])
        return api_response(data={
            "providers": new_settings.list_providers(),
        })


class AdminAIProviderSwitchView(APIView):
    """切换活跃 AI 供应商接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AIProviderSwitchSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        provider_name = serializer.validated_data["provider_name"]
        ai_settings = load_ai_settings()
        if provider_name not in ai_settings.providers:
            return api_response(code=4040, message=f"供应商 '{provider_name}' 不存在", data=None, status_code=404)
        new_settings = update_ai_settings(active_provider=provider_name)
        return api_response(data={
            "active_provider": new_settings.active_provider,
            "providers": new_settings.list_providers(),
        })


class AdminAIProviderDeleteView(APIView):
    """删除 AI 供应商接口（不允许删除当前活跃供应商）。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AIProviderDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        provider_name = serializer.validated_data["provider_name"]
        ai_settings = load_ai_settings()
        if provider_name == ai_settings.active_provider:
            return api_response(code=4093, message="不能删除当前活跃的供应商，请先切换到其他供应商", data=None, status_code=409)
        from config.ai import _load_runtime_config, _save_runtime_config
        runtime = _load_runtime_config()
        runtime["providers"] = [p for p in runtime.get("providers", []) if p.get("name") != provider_name]
        _save_runtime_config(runtime)
        new_settings = load_ai_settings()
        return api_response(data={
            "providers": new_settings.list_providers(),
        })


class AdminAIReportSummaryView(APIView):
    """AI 报表摘要接口：根据订单数据生成运营总结文案。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AIReportSummarySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        orders = BookingOrder.objects.filter(check_in_date__gte=data["start_date"], check_out_date__lte=data["end_date"])
        if data.get("hotel_id"):
            orders = orders.filter(hotel_id=data["hotel_id"])
        total_orders = orders.count()
        total_revenue = orders.filter(payment_status=BookingOrder.PAYMENT_PAID).aggregate(total=Sum("pay_amount"))["total"] or Decimal("0.00")
        summary = f"统计区间内共有 {total_orders} 笔订单，已支付营收 {total_revenue} 元。建议结合取消率与房型均价进一步分析。"
        return api_response(data={"scene": "report_summary", "summary": summary})


class AdminAIReviewSummaryView(APIView):
    """AI 评价摘要接口：聚合评价区间数据并输出洞察总结。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AIReviewSummarySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        reviews = Review.objects.filter(created_at__date__gte=data["start_date"], created_at__date__lte=data["end_date"])
        if data.get("hotel_id"):
            reviews = reviews.filter(hotel_id=data["hotel_id"])
        avg_score = reviews.aggregate(avg=Avg("score"))["avg"] or 0
        summary = f"统计区间内共有 {reviews.count()} 条评价，平均评分 {round(avg_score, 2)} 分。建议重点关注低分评价中的重复问题。"
        return api_response(data={"scene": "review_summary", "summary": summary})


class AdminAIReplySuggestionView(APIView):
    """AI 回复建议接口：基于评价内容生成客服回复建议。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AIReplySuggestionSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        review = Review.objects.filter(id=serializer.validated_data["review_id"]).first()
        if not review:
            return api_response(code=4040, message="评价不存在", data=None, status_code=404)
        suggestion = fallback_ai_reply("reply_suggestion")
        return api_response(data={"scene": "reply_suggestion", "suggested_reply": suggestion})


class AdminReportTasksView(APIView):
    """报表任务接口：查询任务列表并创建示例报表任务。"""
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
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
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


class AdminCouponTemplatesView(APIView):
    """管理端优惠券模板列表/创建接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = CouponTemplate.objects.all()
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=CouponTemplateSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)

    def post(self, request):
        serializer = CouponTemplateCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        tpl = CouponTemplate.objects.create(**serializer.validated_data)
        return api_response(data=CouponTemplateSerializer(tpl).data)


class AdminCouponTemplateUpdateView(APIView):
    """管理端优惠券模板上/下架接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        tpl_id = request.data.get("template_id")
        new_status = request.data.get("status")
        if not tpl_id or new_status not in ("active", "inactive"):
            return api_response(code=4001, message="参数错误", data=None, status_code=400)
        tpl = CouponTemplate.objects.filter(id=tpl_id).first()
        if not tpl:
            return api_response(code=4040, message="模板不存在", data=None, status_code=404)
        tpl.status = new_status
        tpl.save(update_fields=["status", "updated_at"])
        return api_response(data=CouponTemplateSerializer(tpl).data)


class AdminMemberOverviewView(APIView):
    """管理端会员概览接口：各等级人数统计。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        from django.db.models import Count
        level_counts = dict(
            UserProfile.objects.filter(role=UserProfile.ROLE_USER)
            .values("member_level")
            .annotate(cnt=Count("id"))
            .values_list("member_level", "cnt")
        )
        levels = []
        for code, label in UserProfile.MEMBER_LEVEL_CHOICES:
            levels.append({
                "level": code,
                "label": label,
                "count": level_counts.get(code, 0),
                "threshold": UserProfile.MEMBER_THRESHOLDS.get(code, 0),
                "discount_rate": UserProfile.MEMBER_DISCOUNT_RATE.get(code, 1.0),
                "points_multiplier": UserProfile.MEMBER_POINTS_MULTIPLIER.get(code, 1.0),
            })
        total_users = UserProfile.objects.filter(role=UserProfile.ROLE_USER).count()
        return api_response(data={"levels": levels, "total_users": total_users})


class AdminSystemResetView(APIView):
    """系统重置接口：清除所有业务数据，恢复到初始状态。仅系统管理员可用。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = SystemResetSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="请输入 RESET 确认重置", data={"errors": serializer.errors}, status_code=400)

        profile = ensure_profile(request.user)
        if profile.role != UserProfile.ROLE_SYSTEM_ADMIN and not request.user.is_superuser:
            return api_response(code=4030, message="仅系统管理员可以执行重置操作", data=None, status_code=403)

        # 按依赖顺序清除所有业务数据
        from apps.crm.models import (
            CustomerProfile, FavoriteHotel, InvoiceRequest, InvoiceTitle,
            PointsLog, Review, UserCoupon, CouponTemplate,
        )
        from apps.operations.models import AuditLog
        from config.ai import _get_runtime_config_path

        deleted_counts = {}
        deleted_counts["payment_records"] = PaymentRecord.objects.all().delete()[0]
        deleted_counts["invoice_requests"] = InvoiceRequest.objects.all().delete()[0]
        deleted_counts["invoice_titles"] = InvoiceTitle.objects.all().delete()[0]
        deleted_counts["reviews"] = Review.objects.all().delete()[0]
        deleted_counts["booking_orders"] = BookingOrder.objects.all().delete()[0]
        deleted_counts["user_coupons"] = UserCoupon.objects.all().delete()[0]
        deleted_counts["coupon_templates"] = CouponTemplate.objects.all().delete()[0]
        deleted_counts["points_logs"] = PointsLog.objects.all().delete()[0]
        deleted_counts["favorite_hotels"] = FavoriteHotel.objects.all().delete()[0]
        deleted_counts["customer_profiles"] = CustomerProfile.objects.all().delete()[0]
        deleted_counts["room_inventories"] = RoomInventory.objects.all().delete()[0]
        deleted_counts["room_types"] = RoomType.objects.all().delete()[0]
        deleted_counts["hotels"] = Hotel.objects.all().delete()[0]
        deleted_counts["system_notices"] = SystemNotice.objects.all().delete()[0]
        deleted_counts["audit_logs"] = AuditLog.objects.all().delete()[0]
        deleted_counts["report_tasks"] = ReportTask.objects.all().delete()[0]

        # 删除非管理员用户和 Profile
        non_admin_profiles = UserProfile.objects.exclude(
            role__in=[UserProfile.ROLE_SYSTEM_ADMIN, UserProfile.ROLE_HOTEL_ADMIN]
        )
        non_admin_user_ids = list(non_admin_profiles.values_list("user_id", flat=True))
        deleted_counts["user_profiles"] = non_admin_profiles.delete()[0]
        deleted_counts["users"] = User.objects.filter(id__in=non_admin_user_ids).delete()[0]

        # 重置 AI 运行时配置
        ai_config_path = _get_runtime_config_path()
        if ai_config_path.exists():
            ai_config_path.unlink()

        return api_response(data={
            "reset": True,
            "deleted_counts": deleted_counts,
            "message": "系统已重置为初始状态，管理员账号已保留。",
        })

