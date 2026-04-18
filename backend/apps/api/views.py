"""
apps/api/views.py —— 项目所有 REST API 视图类。

按功能分为五组：
  《系统》  ApiRootView / SystemInitCheckView / SystemInitSetupView
  《认证》  UserRegisterView / BaseLoginView / UserLoginView / AdminLoginView /
            RefreshTokenApiView / LogoutApiView / UserAuthMeView
  《公共》  PublicHomeView / PublicHotelsView / PublicHotelSearchSuggestView /
            PublicHotelDetailView / PublicHotelReviewsView / PublicRoomTypeCalendarView /
            CommonCitiesView / CommonDictsView / CommonUploadView / CommonImageThumbView
  《用户》  UserProfileView / UserProfileAvatarView / UserPasswordChangeView /
            UserFavoritesView / UserOrdersView / UserOrderGuestHistoryView /
            UserOrdersDetailView / UserOrdersCreateView / UserOrdersUpdateView /
            UserOrdersPayView / UserOrdersCancelView / UserReviewsCreateView /
            UserReviewsListView / UserPointsLogsView / UserNoticesView /
            UserNoticeUnreadCountView / UserCouponsView / UserAvailableCouponsView /
            UserClaimCouponView / UserOrderAvailableCouponsView / UserInvoicesView /
            UserInvoiceTitleCreateView / UserInvoiceApplyView / UserAIChatView /
            UserAIChatStreamView
  《管理员》  AdminDashboardOverviewView / AdminDashboardChartsView /
            AdminMemberOverviewView / AdminCouponTemplatesView /
            AdminCouponTemplateUpdateView / AdminHotelsView / AdminRoomTypesView /
            AdminInventoryView / AdminOrdersView / AdminOrdersDetailView /
            AdminOrdersChangeStatusView / AdminOrdersCheckInView /
            AdminOrdersCheckOutView / AdminReviewsView / AdminReviewsReplyView /
            AdminUsersView / AdminUsersChangeStatusView / AdminEmployeesView /
            AdminSettingsView / AdminAISettingsView / AdminAIProviderAddView /
            AdminAIProviderSwitchView / AdminAIProviderDeleteView /
            AdminAIReportSummaryView / AdminAIReviewSummaryView /
            AdminAIReplySuggestionView / AdminAIPricingSuggestionView /
            AdminAIBusinessReportView / AdminAIBusinessReportStreamView /
            AdminAIReviewSentimentView / AdminAIMarketingCopyView /
            AdminAIContentGenerateView / AdminAIAnomalyReportView /
            AdminAIOrderAnomalySummaryView / AdminReportTasksView /
            AdminAICallLogsView / AdminAIUsageStatsView / AdminSystemResetView
  《用户AI》  UserAIRecommendationsView / UserAIHotelCompareView /
            UserAISessionsView / UserAISessionMessagesView
"""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path
import hashlib

from django.db import transaction
from django.db.models import F
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.files.storage import default_storage
from django.core.cache import cache
from django.http import HttpResponse
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.crypto import get_random_string
from PIL import Image, UnidentifiedImageError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.settings import api_settings as jwt_api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.api.permissions import IsAdminRole, IsSystemAdminRole, get_user_role
from apps.api.responses import api_response, paginated_response
from apps.api.serializers import (
    AITestSerializer,
    AIChatSerializer,
    AIAnomalyReportSerializer,
    AIBusinessReportSerializer,
    AIOrderAnomalySummarySerializer,
    AICallLogSerializer,
    AIContentGenerateSerializer,
    AIHotelCompareSerializer,
    AIMarketingCopySerializer,
    AIPricingSuggestionSerializer,
    AIProviderCreateSerializer,
    AIProviderDeleteSerializer,
    AIProviderSwitchSerializer,
    AIRecommendationsSerializer,
    AIReplySuggestionSerializer,
    AIReportSummarySerializer,
    AIReviewSentimentSerializer,
    AIReviewSummarySerializer,
    AISettingsUpdateSerializer,
    BookingOrderSerializer,
    ChatMessageSerializer,
    ChatSessionDeleteSerializer,
    ChatSessionSerializer,
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
    OrderExtendStaySerializer,
    OrderSwitchRoomSerializer,
    OrderUpdateSerializer,
    PasswordChangeSerializer,
    PointsLogSerializer,
    PaymentRecordSerializer,
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
    EmployeeUpdateSerializer,
    AdminUserUpdateSerializer,
    CouponTemplateEditSerializer,
    SystemNoticeSerializer,
    SystemResetSerializer,
    UploadSerializer,
    UserCouponSerializer,
    UserProfileSerializer,
)
from apps.bookings.models import BookingOrder
from apps.crm.models import ChatMessage, ChatSession, CouponTemplate, FavoriteHotel, InvoiceRequest, InvoiceTitle, PointsLog, Review, UserCoupon
from apps.hotels.models import Hotel, RoomInventory, RoomType
from apps.operations.models import AICallLog, PlatformConfig, SystemNotice
from apps.operations.services.ai_service import AIChatService
from apps.operations.services.prompt_service import PromptSceneError
from config.ai import load_ai_settings, update_ai_settings, BUILTIN_PROVIDERS
from apps.payments.models import PaymentRecord
from apps.reports.models import ReportTask
from apps.users.models import UserProfile

User = get_user_model()
logger = logging.getLogger(__name__)


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
    with transaction.atomic():
        defaults = {
            "nickname": user.username,
            "mobile": "",
            "role": UserProfile.ROLE_SYSTEM_ADMIN if user.is_superuser else UserProfile.ROLE_USER,
            "status": UserProfile.STATUS_ACTIVE,
        }
        profile, _ = UserProfile.objects.select_for_update().get_or_create(user=user, defaults=defaults)
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


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_IMAGE_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "GIF": ".gif",
}


def get_max_upload_bytes() -> int:
    max_upload_mb = int(getattr(settings, "MAX_UPLOAD_MB", 20))
    return max_upload_mb * 1024 * 1024


def validate_image_upload(file_obj) -> tuple[bool, str | None, str | None]:
    max_upload_bytes = get_max_upload_bytes()
    size = int(getattr(file_obj, "size", 0) or 0)
    if size <= 0:
        return False, "上传文件不能为空", None
    if size > max_upload_bytes:
        return False, f"文件大小不能超过 {max_upload_bytes // (1024 * 1024)}MB", None

    suffix = Path(getattr(file_obj, "name", "")).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        return False, "仅支持 JPG、PNG、WebP、GIF 图片", None

    try:
        file_obj.seek(0)
        with Image.open(file_obj) as image:
            image.verify()
        file_obj.seek(0)
        with Image.open(file_obj) as image:
            image_format = (image.format or "").upper()
    except (UnidentifiedImageError, OSError, ValueError):
        return False, "上传文件不是有效图片", None
    finally:
        try:
            file_obj.seek(0)
        except Exception:
            pass

    normalized_ext = ALLOWED_IMAGE_FORMATS.get(image_format)
    if not normalized_ext:
        return False, "仅支持 JPG、PNG、WebP、GIF 图片", None
    return True, None, normalized_ext


def build_safe_upload_path(prefix: str, extension: str, owner: str | int | None = None) -> str:
    now = timezone.localtime()
    random_name = get_random_string(20, allowed_chars="abcdefghijklmnopqrstuvwxyz0123456789")
    date_path = now.strftime("%Y/%m")
    owner_path = f"{owner}/" if owner is not None and owner != "" else ""
    return f"{prefix}/{owner_path}{date_path}/{random_name}{extension}"


def normalize_display_name(value: str) -> str:
    text = (value or "").strip()
    return " ".join(text.split())


def find_duplicate_hotel(name: str, exclude_id: int | None = None):
    normalized_name = normalize_display_name(name)
    if not normalized_name:
        return None
    queryset = Hotel.objects.filter(name__iexact=normalized_name)
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    return queryset.only("id", "name").first()


def find_duplicate_room_type(hotel_id: int, room_name: str, exclude_id: int | None = None):
    normalized_name = normalize_display_name(room_name)
    if not normalized_name:
        return None
    queryset = RoomType.objects.filter(hotel_id=hotel_id, name__iexact=normalized_name)
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    return queryset.only("id", "name").first()


def is_order_checkout_overdue(order: BookingOrder, *, today=None) -> bool:
    current_day = today or timezone.localdate()
    check_out_date = getattr(order, "check_out_date", None)
    return bool(check_out_date and check_out_date < current_day)


def append_order_operator_remark(order: BookingOrder, message: str) -> bool:
    from apps.bookings.tasks import append_operator_remark

    return append_operator_remark(order, message)


def mask_mobile(mobile: str) -> str:
    value = (mobile or "").strip()
    if len(value) < 7:
        return value
    return f"{value[:3]}***{value[-3:]}"


def _blacklist_user_tokens(user):
    """将用户所有未过期的 Refresh Token 加入黑名单。"""
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
    except Exception:
        pass  # 黑名单功能不可用时静默忽略


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
        "expires_in": int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
    }


def build_refresh_response_payload(refresh: RefreshToken) -> dict:
    """按当前 JWT 策略返回新的 access/refresh token 组合。"""
    refresh_token_value = str(refresh)
    if jwt_api_settings.ROTATE_REFRESH_TOKENS:
        if jwt_api_settings.BLACKLIST_AFTER_ROTATION:
            try:
                refresh.blacklist()
            except Exception:
                pass
        refresh.set_jti()
        refresh.set_exp()
        refresh.set_iat()
        try:
            refresh.outstand()
        except Exception:
            pass
        refresh_token_value = str(refresh)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": refresh_token_value,
        "token_type": "Bearer",
        "expires_in": int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
    }


def revoke_refresh_token(raw_token: str | None) -> bool:
    """将 refresh token 加入黑名单；失败时返回 False。"""
    if not raw_token:
        return False
    try:
        RefreshToken(raw_token).blacklist()
        return True
    except Exception:
        return False


def make_order_no() -> str:
    """生成唯一订单号，格式：HT + 时间戳(14位) + 4位随机数字。"""
    now = timezone.localtime()
    return f"HT{now.strftime('%Y%m%d%H%M%S')}{get_random_string(4, allowed_chars='0123456789')}"


def make_payment_no() -> str:
    """生成唯一支付流水号，格式：PM + 时间戳(14位) + 6位随机数字。"""
    now = timezone.localtime()
    return f"PM{now.strftime('%Y%m%d%H%M%S')}{get_random_string(6, allowed_chars='0123456789')}"


def fallback_ai_reply(scene: str) -> str:
    """
    当 AI 服务未配置或调用失败时返回占位回复文本。

    Args:
        scene: AI 场景标识。
    """
    _FALLBACKS = {
        "customer_service": "您好，这里是 HoteLink 智能客服。当前我暂时无法从系统已接入的数据中生成可靠答复，请稍后重试，或联系人工客服进一步处理。",
        "booking_assistant": "您好，这里是 HoteLink AI 订房助手。当前我暂时无法完成智能筛选，您可以先告诉我城市和预算，我会继续为您定位可预订酒店。",
        "report_summary": "当前时间段内营收与订单波动建议结合入住率、取消率和均价变化综合判断。",
        "review_summary": "近期评价主要关注服务体验、卫生情况和入住便利性，建议优先处理重复出现的问题。",
        "reply_suggestion": "感谢您的反馈，我们会认真优化相关体验，期待您的再次入住。",
        "pricing_suggestion": "建议参考周边竞品价格及历史入住率，适当调整节假日溢价区间。",
        "business_report": "当前数据量不足以生成深度分析报告，建议在数据积累后重试。",
        "marketing_copy": "期待您的入住，我们将为您提供优质的住宿体验。",
        "content_generate": "尊享舒适住宿，品质之选。",
        "review_sentiment": "当前无法进行情感分析，请稍后重试。",
        "anomaly_report": "暂无明显异常，系统运行正常。",
        "recommendations": "暂无个性化推荐，请浏览全部酒店。",
        "hotel_compare": "暂无对比结果，请稍后重试。",
    }
    return _FALLBACKS.get(scene, f"当前为 {scene} 场景的占位回复。")


def _extract_ai_usage_from_result(result: dict | None) -> tuple[int, int, int]:
    """从 AI 返回结果中提取 token 用量，兼容 OpenAI usage 字段。"""
    if not isinstance(result, dict):
        return 0, 0, 0

    raw = result.get("raw")
    usage = {}
    if isinstance(raw, dict):
        usage = raw.get("usage") or {}

    input_tokens = int(usage.get("prompt_tokens") or result.get("input_tokens") or 0)
    output_tokens = int(usage.get("completion_tokens") or result.get("output_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or result.get("total_tokens") or 0)
    if total_tokens <= 0:
        total_tokens = input_tokens + output_tokens
    return input_tokens, output_tokens, total_tokens


def record_ai_call_log(
    *,
    user,
    scene: str,
    service: AIChatService | None = None,
    result: dict | None = None,
    status: str = AICallLog.STATUS_SUCCESS,
    error_message: str = "",
    latency_ms: int = 0,
) -> None:
    """统一写入 AI 调用日志，避免各接口遗漏埋点。"""
    provider = ""
    model = ""
    if isinstance(result, dict):
        provider = str(result.get("provider") or "")
        model = str(result.get("model") or result.get("model_used") or "")

    if service and service.provider:
        provider = provider or (service.provider.name or "")
        model = model or (service.provider.chat_model or "")

    input_tokens, output_tokens, total_tokens = _extract_ai_usage_from_result(result)
    cost_estimate = Decimal("0")
    if isinstance(result, dict):
        raw_cost_estimate = result.get("cost_estimate")
        if raw_cost_estimate not in (None, ""):
            try:
                cost_estimate = Decimal(str(raw_cost_estimate))
            except (InvalidOperation, TypeError, ValueError):
                cost_estimate = Decimal("0")

    try:
        AICallLog.objects.create(
            user=user,
            scene=(scene or "unknown")[:50],
            provider=provider[:50] or "unknown",
            model=model[:100] or "unknown",
            input_tokens=max(0, input_tokens),
            output_tokens=max(0, output_tokens),
            total_tokens=max(0, total_tokens),
            cost_estimate=cost_estimate,
            latency_ms=max(0, int(latency_ms)),
            status=status,
            error_message=(error_message or "")[:5000],
        )
    except Exception:
        logger.exception("Failed to persist AI call log", extra={"scene": scene, "status": status})


def persist_ai_chat_turn(
    *,
    user: User,
    scene: str,
    question: str,
    answer: str,
    session_id: int | None = None,
) -> ChatSession:
    """持久化一轮 AI 对话（用户问题 + 助手回复），并维护会话统计。"""
    normalized_question = (question or "").strip()
    normalized_answer = (answer or "").strip()
    now = timezone.now()

    session = None
    if session_id:
        session = ChatSession.objects.filter(id=session_id, user=user).first()

    if session is None:
        title_source = normalized_question or normalized_answer or "新会话"
        session = ChatSession.objects.create(
            user=user,
            scene=scene,
            title=title_source[:200],
            message_count=0,
            last_message_at=now,
        )
    else:
        update_fields = []
        if session.scene != scene:
            session.scene = scene
            update_fields.append("scene")
        if not session.title and normalized_question:
            session.title = normalized_question[:200]
            update_fields.append("title")
        if update_fields:
            update_fields.append("updated_at")
            session.save(update_fields=update_fields)

    pending_messages = []
    if normalized_question:
        pending_messages.append(
            ChatMessage(
                session=session,
                role=ChatMessage.ROLE_USER,
                content=normalized_question,
            )
        )
    if normalized_answer:
        pending_messages.append(
            ChatMessage(
                session=session,
                role=ChatMessage.ROLE_ASSISTANT,
                content=normalized_answer,
            )
        )
    if pending_messages:
        ChatMessage.objects.bulk_create(pending_messages)

    message_count = ChatMessage.objects.filter(session=session).count()
    session.message_count = message_count
    session.last_message_at = now
    session.save(update_fields=["message_count", "last_message_at", "updated_at"])
    return session


def get_dict_payload() -> dict:
    """返回系统内置字典数据，包括酒店星级、支付方式、床型等列举选项。"""
    return {
        "hotel_star": [{"label": f"{i} 星", "value": i} for i in [2, 3, 4, 5]],
        "hotel_type": [
            {"label": "酒店", "value": "hotel"},
            {"label": "民宿", "value": "homestay"},
            {"label": "短租", "value": "short_rent"},
        ],
        "hotel_facility": [
            {"label": "WiFi", "value": "wifi"},
            {"label": "停车场", "value": "parking"},
            {"label": "泳池", "value": "pool"},
            {"label": "健身房", "value": "gym"},
            {"label": "餐厅", "value": "restaurant"},
            {"label": "空调", "value": "air_conditioning"},
            {"label": "电梯", "value": "elevator"},
            {"label": "洗衣服务", "value": "laundry"},
            {"label": "行李寄存", "value": "luggage_storage"},
            {"label": "24小时前台", "value": "front_desk_24h"},
            {"label": "接机服务", "value": "airport_shuttle"},
            {"label": "会议室", "value": "meeting_room"},
            {"label": "无烟房", "value": "non_smoking"},
            {"label": "宠物友好", "value": "pet_friendly"},
            {"label": "厨房", "value": "kitchen"},
            {"label": "洗衣机", "value": "washing_machine"},
        ],
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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)

        data = serializer.validated_data
        with transaction.atomic():
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
        has_admin = UserProfile.objects.filter(role=UserProfile.ROLE_SYSTEM_ADMIN).exists()
        return api_response(data={"initialized": has_admin})


class SystemInitSetupView(APIView):
    """系统首次初始化：创建首个系统管理员并返回登录令牌。"""
    """首次初始化：创建管理员账号（仅当系统中无管理员时可用）"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "system_init"

    def post(self, request):
        has_admin = UserProfile.objects.filter(role=UserProfile.ROLE_SYSTEM_ADMIN).exists()
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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"
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
        if profile.status != UserProfile.STATUS_ACTIVE:
            return api_response(code=4031, message="账号已被禁用或锁定，请联系管理员", data=None, status_code=403)
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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_refresh"

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return api_response(code=4002, message="缺少 refresh_token", data=None, status_code=400)
        try:
            refresh = RefreshToken(refresh_token)
            return api_response(data=build_refresh_response_payload(refresh))
        except Exception:
            return api_response(code=4011, message="Token 无效", data=None, status_code=401)


class LogoutApiView(APIView):
    """退出登录接口：尽量回收 refresh token，缩短被盗令牌可被滥用的窗口。"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_logout"

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        revoked = revoke_refresh_token(refresh_token)
        return api_response(data={"logged_out": True, "refresh_revoked": revoked})


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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "upload"

    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        file_obj = serializer.validated_data["file"]
        scene = serializer.validated_data["scene"]
        valid, error_message, extension = validate_image_upload(file_obj)
        if not valid:
            return api_response(code=4001, message=error_message or "上传失败", data=None, status_code=400)

        path = default_storage.save(
            build_safe_upload_path(prefix=f"uploads/{scene}", extension=extension or ".jpg"),
            file_obj,
        )
        file_url = f"{settings.MEDIA_URL}{path}"
        return api_response(data={"file_name": Path(path).name, "file_url": file_url, "scene": scene})


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

        try:
            cache_path.write_bytes(content)
        except OSError:
            logger.warning("thumbnail cache write failed for %s", source_path, exc_info=True)
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
        hotel_type = request.query_params.get("type")
        facilities = request.query_params.get("facilities")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        sort = request.query_params.get("sort", "default")

        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(address__icontains=keyword))
        if city:
            queryset = queryset.filter(city=city)
        if star:
            queryset = queryset.filter(star=star)
        if hotel_type and hotel_type in {Hotel.TYPE_HOTEL, Hotel.TYPE_HOMESTAY, Hotel.TYPE_SHORT_RENT}:
            queryset = queryset.filter(type=hotel_type)
        if facilities:
            for fac in [f.strip() for f in facilities.split(",") if f.strip()]:
                queryset = queryset.filter(facilities__contains=fac)
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
            hotel = Hotel.objects.prefetch_related("room_types").get(pk=hotel_id, status=Hotel.STATUS_ONLINE)
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
        valid, error_message, extension = validate_image_upload(file_obj)
        if not valid:
            return api_response(code=4001, message=error_message or "头像上传失败", data=None, status_code=400)
        path = default_storage.save(
            build_safe_upload_path(prefix="avatars", owner=request.user.id, extension=extension or ".jpg"),
            file_obj,
        )
        profile = ensure_profile(request.user)
        profile.avatar = f"{settings.MEDIA_URL}{path}"
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
        # 撤销该用户所有未过期的 Refresh Token，防止旧 Token 继续使用
        _blacklist_user_tokens(request.user)
        new_tokens = build_tokens_for_user(request.user)
        return api_response(data={"changed": True, **new_tokens})


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
        queryset = BookingOrder.objects.filter(user=request.user).select_related("hotel", "room_type").prefetch_related("payments")
        status_param = request.query_params.get("status")
        if status_param:
            statuses = [s.strip() for s in status_param.split(",") if s.strip()]
            if len(statuses) == 1:
                queryset = queryset.filter(status=statuses[0])
            elif statuses:
                queryset = queryset.filter(status__in=statuses)

        payment_status_param = request.query_params.get("payment_status")
        if payment_status_param:
            queryset = queryset.filter(payment_status=payment_status_param)

        keyword = str(request.query_params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(order_no__icontains=keyword)
                | Q(hotel__name__icontains=keyword)
                | Q(room_type__name__icontains=keyword)
                | Q(guest_name__icontains=keyword)
                | Q(guest_mobile__icontains=keyword)
            )

        errors: dict[str, list[str]] = {}

        def parse_date_param(name: str):
            raw = request.query_params.get(name)
            if not raw:
                return None
            parsed = parse_date(raw)
            if parsed is None:
                errors.setdefault(name, []).append("日期格式错误，应为 YYYY-MM-DD")
            return parsed

        def parse_amount_param(name: str):
            raw = request.query_params.get(name)
            if raw in (None, ""):
                return None
            try:
                value = Decimal(str(raw))
            except (InvalidOperation, TypeError, ValueError):
                errors.setdefault(name, []).append("金额格式错误")
                return None
            if value < 0:
                errors.setdefault(name, []).append("金额不能为负数")
                return None
            return value

        check_in_start = parse_date_param("check_in_start")
        check_in_end = parse_date_param("check_in_end")
        created_start = parse_date_param("created_start")
        created_end = parse_date_param("created_end")
        amount_min = parse_amount_param("amount_min")
        amount_max = parse_amount_param("amount_max")

        if check_in_start and check_in_end and check_in_start > check_in_end:
            errors.setdefault("check_in_range", []).append("入住开始日期不能晚于结束日期")
        if created_start and created_end and created_start > created_end:
            errors.setdefault("created_range", []).append("下单开始日期不能晚于结束日期")
        if amount_min is not None and amount_max is not None and amount_min > amount_max:
            errors.setdefault("amount_range", []).append("最低金额不能大于最高金额")

        if errors:
            return api_response(code=4001, message="参数错误", data={"errors": errors}, status_code=400)

        if check_in_start:
            queryset = queryset.filter(check_in_date__gte=check_in_start)
        if check_in_end:
            queryset = queryset.filter(check_in_date__lte=check_in_end)
        if created_start:
            queryset = queryset.filter(created_at__date__gte=created_start)
        if created_end:
            queryset = queryset.filter(created_at__date__lte=created_end)
        if amount_min is not None:
            queryset = queryset.filter(pay_amount__gte=amount_min)
        if amount_max is not None:
            queryset = queryset.filter(pay_amount__lte=amount_max)

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
        order = BookingOrder.objects.filter(id=order_id, user=request.user).select_related("hotel", "room_type").prefetch_related("payments").first()
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
        if data["check_in_date"] < timezone.localdate():
            return api_response(code=4001, message="入住日期不能早于今天", data=None, status_code=400)

        # 1. 会员折扣
        profile = ensure_profile(request.user)
        member_discount_rate = Decimal(str(profile.discount_rate))

        # 2. 优惠券：在事务内加行锁，防止同一张券被并发订单同时核销
        coupon_discount_amount = Decimal("0.00")
        coupon_obj = None
        coupon_id = data.get("coupon_id")

        with transaction.atomic():
            # 0. 库存校验与扣减（行锁防并发超卖）
            date_range = [data["check_in_date"] + timedelta(days=i) for i in range(nights)]
            inventories = list(
                RoomInventory.objects.select_for_update()
                .filter(room_type=room_type, date__in=date_range, status="available")
            )
            inv_map = {inv.date: inv for inv in inventories}
            for d in date_range:
                inv = inv_map.get(d)
                if not inv or inv.stock <= 0:
                    return api_response(code=4003, message=f"{d} 库存不足", data=None, status_code=400)
            for inv in inventories:
                inv.stock -= 1
                inv.save(update_fields=["stock", "updated_at"])

            # 使用按日库存价格计算总价（支持动态定价）
            original_amount = sum(inv_map[d].price for d in date_range)
            if original_amount <= 0:
                original_amount = room_type.base_price * nights

            member_discounted = (original_amount * member_discount_rate).quantize(Decimal("0.01"))
            member_discount_amount = original_amount - member_discounted

            if coupon_id:
                from django.utils import timezone as tz
                today = tz.localdate()
                coupon_obj = UserCoupon.objects.select_for_update().filter(
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

            # 自动取消未支付订单（提交后触发，避免事务未提交时 Celery 已执行）
            cancel_minutes = PlatformConfig.load().order_auto_cancel_minutes
            from apps.bookings.tasks import auto_cancel_unpaid_order
            transaction.on_commit(
                lambda: auto_cancel_unpaid_order.apply_async(args=[order.id], countdown=cancel_minutes * 60)
            )

        SystemNotice.objects.create(
            user=request.user,
            notice_type=SystemNotice.TYPE_ORDER,
            title="订单创建成功",
            content=f"订单 {order.order_no} 已创建，请在{cancel_minutes}分钟内完成支付，逾期将自动取消。",
            related_order=order,
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
        if order.status in {BookingOrder.STATUS_COMPLETED, BookingOrder.STATUS_CANCELLED, BookingOrder.STATUS_REFUNDED}:
            return api_response(code=4093, message="当前订单状态不允许修改", data=None, status_code=409)
        updated_fields = []
        for field in ["guest_name", "guest_mobile", "remark"]:
            if field in data:
                setattr(order, field, data[field])
                updated_fields.append(field)
        if updated_fields:
            updated_fields.append("updated_at")
            order.save(update_fields=updated_fields)
        return api_response(data=BookingOrderSerializer(order).data)


class UserOrdersPayView(APIView):
    """用户订单支付接口：创建支付记录并更新订单支付状态。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderPaySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data

        from apps.bookings.tasks import cancel_timeout_unpaid_order
        cancel_minutes = PlatformConfig.load().order_auto_cancel_minutes

        # 使用行锁确保同一订单的支付操作原子性，防止并发重复支付
        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(id=data["order_id"], user=request.user).first()
            if not order:
                return api_response(code=4040, message="订单不存在", data=None, status_code=404)
            if order.payment_status == BookingOrder.PAYMENT_PAID:
                return api_response(code=4093, message="订单已支付", data=None, status_code=409)
            if order.status != BookingOrder.STATUS_PENDING_PAYMENT:
                return api_response(code=4093, message="当前订单状态不允许支付", data=None, status_code=409)

            timeout_deadline = order.created_at + timedelta(minutes=cancel_minutes)
            if timezone.now() >= timeout_deadline:
                cancelled = cancel_timeout_unpaid_order(order, cancel_minutes=cancel_minutes)
                if cancelled:
                    return api_response(code=4093, message="订单已超时未支付，已自动取消，请重新下单", data=None, status_code=409)
                return api_response(code=4093, message="当前订单状态不允许支付", data=None, status_code=409)

            payment = PaymentRecord.objects.create(
                order=order,
                payment_no=make_payment_no(),
                method=data["payment_method"],
                status=PaymentRecord.STATUS_PAID,
                amount=order.pay_amount,
                paid_at=timezone.now(),
            )
            paid_at = payment.paid_at or timezone.now()
            order.payment_status = BookingOrder.PAYMENT_PAID
            order.status = BookingOrder.STATUS_PAID
            if not order.paid_at:
                order.paid_at = paid_at
            # 支付成功后奖励积分（事务内，保证一致性）
            profile = ensure_profile(request.user)
            base_points = int(order.pay_amount / Decimal("10"))
            earned_points = int(base_points * Decimal(str(profile.points_multiplier))) if base_points > 0 else 0
            if earned_points > 0:
                order.points_earned = earned_points
                order.save(update_fields=["payment_status", "status", "paid_at", "points_earned", "updated_at"])
                add_points(
                    request.user, earned_points, PointsLog.TYPE_CONSUME_REWARD,
                    f"订单 {order.order_no} 消费奖励（{profile.points_multiplier}x倍率）",
                    order=order,
                )
            else:
                order.save(update_fields=["payment_status", "status", "paid_at", "updated_at"])

        SystemNotice.objects.create(
            user=request.user,
            notice_type=SystemNotice.TYPE_PAYMENT,
            title="支付成功",
            content=f"订单 {order.order_no} 已完成支付。",
            related_order=order,
        )
        return api_response(data={"order_id": order.id, "payment_id": payment.id, "payment_status": order.payment_status})


class UserOrdersCancelView(APIView):
    """用户取消订单接口：限制已入住/已完成/已取消/退款中/已退款订单不可取消。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCancelSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data

        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(id=data["order_id"], user=request.user).first()
            if not order:
                return api_response(code=4040, message="订单不存在", data=None, status_code=404)
            non_cancellable = {
                BookingOrder.STATUS_COMPLETED, BookingOrder.STATUS_CANCELLED,
                BookingOrder.STATUS_CHECKED_IN, BookingOrder.STATUS_REFUNDING,
                BookingOrder.STATUS_REFUNDED,
            }
            if order.status in non_cancellable:
                return api_response(code=4093, message="当前状态不允许取消", data=None, status_code=409)

            was_paid = order.payment_status == BookingOrder.PAYMENT_PAID
            order.status = BookingOrder.STATUS_CANCELLED
            order.cancelled_at = timezone.now()
            update_fields = ["status", "cancelled_at", "updated_at"]

            reason = data.get("reason", "")
            if reason and append_order_operator_remark(order, reason):
                update_fields.append("operator_remark")

            # 已支付订单取消时处理退款
            if was_paid:
                order.payment_status = BookingOrder.PAYMENT_REFUNDED
                update_fields.append("payment_status")
                PaymentRecord.objects.filter(
                    order=order, status=PaymentRecord.STATUS_PAID,
                ).update(status=PaymentRecord.STATUS_REFUNDED)

            order.save(update_fields=update_fields)

            # 归还库存
            nights = (order.check_out_date - order.check_in_date).days
            date_range = [order.check_in_date + timedelta(days=i) for i in range(nights)]
            RoomInventory.objects.filter(
                room_type_id=order.room_type_id, date__in=date_range,
            ).update(stock=F("stock") + 1)
            # 归还优惠券
            if order.coupon_id:
                UserCoupon.objects.filter(
                    pk=order.coupon_id,
                    status=UserCoupon.STATUS_USED,
                    used_order_id=order.id,
                ).update(status=UserCoupon.STATUS_UNUSED, used_order=None, used_at=None)
            # 已支付订单取消时回收积分
            if was_paid and order.points_earned > 0:
                add_points(
                    order.user, -order.points_earned, PointsLog.TYPE_CONSUME_REWARD,
                    f"订单 {order.order_no} 取消，回收消费积分",
                    order=order,
                )
                order.points_earned = 0
                order.save(update_fields=["points_earned"])

        return api_response(data={"order_id": order.id, "status": order.status})


class UserReviewsCreateView(APIView):
    """用户评价创建接口：仅限已完成订单，首评按内容质量分级奖励积分。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        order = BookingOrder.objects.filter(id=data["order_id"], user=request.user).select_related("hotel").first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        if order.status != "completed":
            return api_response(code=4003, message="只有已完成的订单才可以评价", data=None, status_code=403)
        images = data.get("images") or []
        review, created = Review.objects.update_or_create(
            order=order,
            defaults={
                "user": request.user,
                "hotel": order.hotel,
                "score": data["score"],
                "content": data["content"],
                "images": images,
            },
        )
        points_awarded = 0
        if created:
            char_len = len(data["content"].strip())
            has_images = len(images) > 0
            if char_len >= 100 and has_images:
                points_earned = 10
            elif char_len >= 50 and has_images:
                points_earned = 7
            elif char_len >= 50:
                points_earned = 5
            else:
                points_earned = 0
            if points_earned > 0:
                add_points(request.user, points_earned, PointsLog.TYPE_REVIEW_REWARD, f"评价订单 {order.order_no} 奖励", order=order)
                points_awarded = points_earned
                SystemNotice.objects.create(
                    user=request.user,
                    notice_type=SystemNotice.TYPE_MEMBER,
                    title="评价积分奖励",
                    content=f"感谢您对「{order.hotel.name}」的评价，已奖励 {points_earned} 积分！",
                )
        return api_response(data={"review_id": review.id, "score": review.score, "points_awarded": points_awarded})


class UserReviewsListView(APIView):
    """用户自己的评价列表。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Review.objects.filter(user=request.user)
            .select_related("hotel", "order")
            .order_by("-created_at")
        )
        page, page_size = get_page_params(request)
        total = qs.count()
        items = qs[(page - 1) * page_size: page * page_size]
        data = []
        for r in items:
            data.append({
                "id": r.id,
                "hotel_id": r.hotel_id,
                "hotel_name": r.hotel.name if r.hotel else "",
                "room_type_name": r.order.room_type_name if r.order and hasattr(r.order, "room_type_name") else "",
                "score": r.score,
                "content": r.content,
                "images": r.images or [],
                "reply": r.reply_content or "",
                "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
            })
        return paginated_response(items=data, page=page, page_size=page_size, total=total)


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
        """标记通知已读/未读：action='read'（默认）标记已读，action='unread' 标记未读；ids=[] 指定，不传则操作全部。"""
        ids = request.data.get("ids")
        action = request.data.get("action", "read")
        queryset = SystemNotice.objects.filter(user=request.user)
        if ids:
            queryset = queryset.filter(id__in=ids)
        if action == "unread":
            queryset.update(is_read=False)
        else:
            queryset.filter(is_read=False).update(is_read=True)
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
        with transaction.atomic():
            tpl = CouponTemplate.objects.select_for_update().filter(id=serializer.validated_data["template_id"]).first()
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
        if InvoiceRequest.objects.filter(order=order).exists():
            return api_response(code=4090, message="该订单已存在发票申请，请勿重复提交", data=None, status_code=409)
        invoice_request = InvoiceRequest.objects.create(order=order, invoice_title=title)
        return api_response(data=InvoiceRequestSerializer(invoice_request).data)


class UserInvoiceTitleUpdateView(APIView):
    """用户编辑发票抬头接口。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title_id = request.data.get("title_id")
        if not title_id:
            return api_response(code=4001, message="缺少 title_id 参数", data=None, status_code=400)
        title = InvoiceTitle.objects.filter(id=title_id, user=request.user).first()
        if not title:
            return api_response(code=4040, message="发票抬头不存在", data=None, status_code=404)
        serializer = InvoiceTitleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        for field, value in serializer.validated_data.items():
            setattr(title, field, value)
        title.save()
        return api_response(data=InvoiceTitleSerializer(title).data)


class UserInvoiceTitleDeleteView(APIView):
    """用户删除发票抬头接口。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title_id = request.data.get("title_id")
        if not title_id:
            return api_response(code=4001, message="缺少 title_id 参数", data=None, status_code=400)
        title = InvoiceTitle.objects.filter(id=title_id, user=request.user).first()
        if not title:
            return api_response(code=4040, message="发票抬头不存在", data=None, status_code=404)
        if InvoiceRequest.objects.filter(invoice_title=title).exists():
            return api_response(code=4091, message="该抬头已有关联开票记录，无法删除", data=None, status_code=409)
        title.delete()
        return api_response(data={"title_id": title_id, "deleted": True})


class UserAIChatView(APIView):
    """用户 AI 客服接口：优先调用模型服务，失败时返回兜底文案。"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_user"

    def post(self, request):
        serializer = AIChatSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        started_at = time.perf_counter()
        try:
            result = service.reply_customer_service(
                user=request.user,
                scene=data["scene"],
                question=data["question"],
                hotel_id=data.get("hotel_id"),
                order_id=data.get("order_id"),
                booking_context=data.get("booking_context"),
                conversation_summary=data.get("conversation_summary") or "",
            )
        except PromptSceneError as exc:
            return api_response(code=4002, message=str(exc), data=None, status_code=400)

        answer = result["answer"] or fallback_ai_reply(result["scene"])
        ai_status = AICallLog.STATUS_SUCCESS if result["answer"] else AICallLog.STATUS_FAILED
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        record_ai_call_log(
            user=request.user,
            scene=result["scene"],
            service=service,
            result=result,
            status=ai_status,
            latency_ms=latency_ms,
        )
        session = persist_ai_chat_turn(
            user=request.user,
            scene=result["scene"],
            question=data["question"],
            answer=answer,
            session_id=data.get("session_id"),
        )
        return api_response(
            data={
                "answer": answer,
                "scene": result["scene"],
                "booking_assistant": result.get("booking_assistant"),
                "session_id": session.id,
            }
        )


class UserAIChatStreamView(APIView):
    """用户 AI 客服流式接口：以 SSE 格式逐 token 推送回复内容。"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_user"

    def post(self, request):
        import json
        from django.http import StreamingHttpResponse

        serializer = AIChatSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        started_at = time.perf_counter()
        try:
            result = service.reply_customer_service(
                user=request.user,
                scene=data["scene"],
                question=data["question"],
                hotel_id=data.get("hotel_id"),
                order_id=data.get("order_id"),
                booking_context=data.get("booking_context"),
                conversation_summary=data.get("conversation_summary") or "",
            )
        except PromptSceneError as exc:
            return api_response(code=4002, message=str(exc), data=None, status_code=400)

        scene = result["scene"]
        answer = result["answer"] or fallback_ai_reply(scene)
        ai_status = AICallLog.STATUS_SUCCESS if result["answer"] else AICallLog.STATUS_FAILED
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        record_ai_call_log(
            user=request.user,
            scene=scene,
            service=service,
            result=result,
            status=ai_status,
            latency_ms=latency_ms,
        )
        booking_assistant = result.get("booking_assistant")
        session = persist_ai_chat_turn(
            user=request.user,
            scene=scene,
            question=data["question"],
            answer=answer,
            session_id=data.get("session_id"),
        )

        def event_stream():
            try:
                meta_payload = {"type": "meta", "scene": scene, "session_id": session.id}
                if booking_assistant is not None:
                    meta_payload["booking_assistant"] = booking_assistant
                yield f"data: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"

                for chunk in service.iter_text_chunks(answer):
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'done': False}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'content': '', 'done': True, 'session_id': session.id}, ensure_ascii=False)}\n\n"
            except Exception:
                fallback = fallback_ai_reply(scene)
                yield f"data: {json.dumps({'type': 'chunk', 'content': fallback, 'done': False}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'content': '', 'done': True}, ensure_ascii=False)}\n\n"

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
        occupied = BookingOrder.objects.filter(
            status=BookingOrder.STATUS_CHECKED_IN,
            check_in_date__lte=today,
            check_out_date__gt=today,
        ).count()
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
        from django.db.models.functions import TruncDate

        end_date = parse_date(request.query_params.get("end_date", "")) or timezone.localdate()
        start_date = parse_date(request.query_params.get("start_date", "")) or (end_date - timedelta(days=6))

        # 单次聚合查询：按日期分组统计订单量
        order_stats = dict(
            BookingOrder.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(cnt=Count("id"))
            .values_list("day", "cnt")
        )
        # 单次聚合查询：按日期分组统计已支付营收
        revenue_stats = dict(
            BookingOrder.objects.filter(
                created_at__date__gte=start_date, created_at__date__lte=end_date,
                payment_status=BookingOrder.PAYMENT_PAID,
            )
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Sum("pay_amount"))
            .values_list("day", "total")
        )

        items = []
        current = start_date
        while current <= end_date:
            items.append({
                "date": current.strftime("%Y-%m-%d"),
                "order_count": order_stats.get(current, 0),
                "revenue": float(revenue_stats.get(current, Decimal("0.00"))),
            })
            current += timedelta(days=1)
        return api_response(data={"items": items})


class AdminHotelsView(APIView):
    """酒店管理接口：列表查询、创建、更新（hotel_admin 可操作），删除（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    _HOTEL_ORDERING_WHITELIST = {"id", "-id", "name", "-name", "city", "-city", "star", "-star", "min_price", "-min_price", "type", "-type"}

    def get(self, request):
        queryset = Hotel.objects.all()
        keyword = (request.query_params.get("keyword") or "").strip()
        status = (request.query_params.get("status") or "").strip()
        hotel_type = (request.query_params.get("type") or "").strip()
        ordering = (request.query_params.get("ordering") or "-id").strip() or "-id"
        thumb_width, thumb_height = parse_thumb_params(request)
        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(address__icontains=keyword))
        if status:
            queryset = queryset.filter(status=status)
        if hotel_type and hotel_type in {Hotel.TYPE_HOTEL, Hotel.TYPE_HOMESTAY, Hotel.TYPE_SHORT_RENT}:
            queryset = queryset.filter(type=hotel_type)
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
            normalized_name = normalize_display_name(serializer.validated_data.get("name", ""))
            if not normalized_name:
                return api_response(
                    code=4001,
                    message="酒店名称不能为空",
                    data={"errors": {"name": ["酒店名称不能为空"]}},
                    status_code=400,
                )
            duplicate = find_duplicate_hotel(normalized_name)
            if duplicate:
                return api_response(
                    code=4090,
                    message="酒店名称已存在，请勿重复创建",
                    data={"errors": {"name": ["酒店名称已存在"]}},
                    status_code=409,
                )
            serializer.validated_data["name"] = normalized_name
            hotel = serializer.save()
            return api_response(data=HotelSimpleSerializer(hotel).data)
        if request.path.endswith("/update"):
            serializer = HotelUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
            hotel = Hotel.objects.filter(pk=serializer.validated_data["hotel_id"]).first()
            if not hotel:
                return api_response(code=4040, message="酒店不存在", data=None, status_code=404)
            if "name" in serializer.validated_data:
                normalized_name = normalize_display_name(serializer.validated_data.get("name", ""))
                if not normalized_name:
                    return api_response(
                        code=4001,
                        message="酒店名称不能为空",
                        data={"errors": {"name": ["酒店名称不能为空"]}},
                        status_code=400,
                    )
                duplicate = find_duplicate_hotel(normalized_name, exclude_id=hotel.id)
                if duplicate:
                    return api_response(
                        code=4090,
                        message="酒店名称已存在，请勿重复创建",
                        data={"errors": {"name": ["酒店名称已存在"]}},
                        status_code=409,
                    )
                serializer.validated_data["name"] = normalized_name
            for field, value in serializer.validated_data.items():
                if field != "hotel_id":
                    setattr(hotel, field, value)
            # 下架/草稿状态变更前检查活跃订单
            if hotel.status != Hotel.STATUS_ONLINE and getattr(hotel, '_original_status', hotel.status) == Hotel.STATUS_ONLINE:
                pass  # 新状态已经不是 online，需要检查
            new_status = serializer.validated_data.get("status")
            if new_status and new_status != Hotel.STATUS_ONLINE:
                has_active = BookingOrder.objects.filter(hotel=hotel).exclude(
                    status__in=[BookingOrder.STATUS_CANCELLED, BookingOrder.STATUS_COMPLETED, BookingOrder.STATUS_REFUNDED]
                ).exists()
                if has_active:
                    return api_response(code=4091, message="该酒店存在未完结订单，无法下架", data=None, status_code=409)
            hotel.save()
            return api_response(data=HotelSimpleSerializer(hotel).data)
        if not request.path.endswith("/delete"):
            return api_response(code=4001, message="未知操作", data=None, status_code=400)
        if get_user_role(request.user) != "system_admin":
            return api_response(code=4030, message="仅系统管理员可以删除酒店", data=None, status_code=403)
        hotel_id = request.data.get("hotel_id")
        if not Hotel.objects.filter(pk=hotel_id).exists():
            return api_response(code=4040, message="酒店不存在", data=None, status_code=404)
        active_orders = BookingOrder.objects.filter(
            hotel_id=hotel_id
        ).exclude(
            status__in=[BookingOrder.STATUS_CANCELLED, BookingOrder.STATUS_COMPLETED, BookingOrder.STATUS_REFUNDED]
        ).exists()
        if active_orders:
            return api_response(code=4091, message="该酒店存在未完结订单，无法删除", data=None, status_code=409)
        Hotel.objects.filter(pk=hotel_id).delete()
        return api_response(data={"hotel_id": hotel_id, "deleted": True})


class AdminHotelsBatchUpdateView(APIView):
    """酒店批量更新接口：批量修改酒店类型等属性。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        hotel_ids = request.data.get("hotel_ids", [])
        if not isinstance(hotel_ids, list) or not hotel_ids:
            return api_response(code=4001, message="hotel_ids 不能为空", data=None, status_code=400)
        updates = {}
        hotel_type = request.data.get("type")
        if hotel_type:
            if hotel_type not in {Hotel.TYPE_HOTEL, Hotel.TYPE_HOMESTAY, Hotel.TYPE_SHORT_RENT}:
                return api_response(code=4001, message="无效的酒店类型", data=None, status_code=400)
            updates["type"] = hotel_type
        if not updates:
            return api_response(code=4001, message="未指定任何更新字段", data=None, status_code=400)
        count = Hotel.objects.filter(pk__in=hotel_ids).update(**updates)
        return api_response(data={"updated_count": count})


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
            hotel_id = int(serializer.validated_data["hotel"].id)
            normalized_name = normalize_display_name(serializer.validated_data.get("name", ""))
            if not normalized_name:
                return api_response(
                    code=4001,
                    message="房型名称不能为空",
                    data={"errors": {"name": ["房型名称不能为空"]}},
                    status_code=400,
                )
            duplicate = find_duplicate_room_type(hotel_id=hotel_id, room_name=normalized_name)
            if duplicate:
                return api_response(
                    code=4090,
                    message="该酒店下已存在同名房型，请勿重复创建",
                    data={"errors": {"name": ["该酒店下已存在同名房型"]}},
                    status_code=409,
                )
            serializer.validated_data["name"] = normalized_name
            room_type = serializer.save()
            return api_response(data=RoomTypeSerializer(room_type).data)
        if request.path.endswith("/update"):
            serializer = RoomTypeUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
            room_type = RoomType.objects.filter(pk=serializer.validated_data["room_type_id"]).first()
            if not room_type:
                return api_response(code=4040, message="房型不存在", data=None, status_code=404)
            next_hotel_id = int(serializer.validated_data.get("hotel", room_type.hotel).id)
            if "name" in serializer.validated_data:
                normalized_name = normalize_display_name(serializer.validated_data.get("name", ""))
                if not normalized_name:
                    return api_response(
                        code=4001,
                        message="房型名称不能为空",
                        data={"errors": {"name": ["房型名称不能为空"]}},
                        status_code=400,
                    )
                duplicate = find_duplicate_room_type(
                    hotel_id=next_hotel_id,
                    room_name=normalized_name,
                    exclude_id=room_type.id,
                )
                if duplicate:
                    return api_response(
                        code=4090,
                        message="该酒店下已存在同名房型，请勿重复创建",
                        data={"errors": {"name": ["该酒店下已存在同名房型"]}},
                        status_code=409,
                    )
                serializer.validated_data["name"] = normalized_name
            for field, value in serializer.validated_data.items():
                if field != "room_type_id":
                    setattr(room_type, field, value)
            room_type.save()
            return api_response(data=RoomTypeSerializer(room_type).data)
        room_type_id = request.data.get("room_type_id")
        if not RoomType.objects.filter(pk=room_type_id).exists():
            return api_response(code=4040, message="房型不存在", data=None, status_code=404)
        active_orders = BookingOrder.objects.filter(
            room_type_id=room_type_id
        ).exclude(
            status__in=[BookingOrder.STATUS_CANCELLED, BookingOrder.STATUS_COMPLETED, BookingOrder.STATUS_REFUNDED]
        ).exists()
        if active_orders:
            return api_response(code=4091, message="该房型存在未完结订单，无法删除", data=None, status_code=409)
        RoomType.objects.filter(pk=room_type_id).delete()
        return api_response(data={"room_type_id": room_type_id, "deleted": True})


class AdminInventoryView(APIView):
    """库存日历管理接口：按日期和房型查询，并支持单日库存更新。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        room_type_id = request.query_params.get("room_type_id")
        start_date = parse_date(request.query_params.get("start_date", ""))
        end_date = parse_date(request.query_params.get("end_date", ""))
        if room_type_id and start_date and end_date and start_date > end_date:
            return api_response(code=4001, message="开始日期不能晚于结束日期", data=None, status_code=400)

        if room_type_id and start_date and end_date:
            with transaction.atomic():
                room_type = RoomType.objects.select_for_update().filter(pk=room_type_id).first()
                if room_type:
                    existing_dates = set(
                        RoomInventory.objects.filter(
                            room_type_id=room_type_id,
                            date__gte=start_date,
                            date__lte=end_date,
                        ).values_list("date", flat=True)
                    )
                    to_create = []
                    current = start_date
                    while current <= end_date:
                        if current not in existing_dates:
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
                    if to_create:
                        RoomInventory.objects.bulk_create(to_create)
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
        with transaction.atomic():
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

    _ORDERING_WHITELIST = {
        "id", "-id",
        "order_no", "-order_no",
        "guest_name", "-guest_name",
        "guest_mobile", "-guest_mobile",
        "hotel__name", "-hotel__name",
        "room_type__name", "-room_type__name",
        "check_in_date", "-check_in_date",
        "check_out_date", "-check_out_date",
        "pay_amount", "-pay_amount",
        "status", "-status",
        "payment_status", "-payment_status",
        "created_at", "-created_at",
        "updated_at", "-updated_at",
    }

    def get(self, request):
        queryset = BookingOrder.objects.select_related("hotel", "room_type", "user").prefetch_related("payments")
        keyword = request.query_params.get("keyword")
        status = request.query_params.get("status")
        ordering = request.query_params.get("ordering", "-id")
        if keyword:
            queryset = queryset.filter(
                Q(order_no__icontains=keyword)
                | Q(guest_mobile__icontains=keyword)
                | Q(guest_name__icontains=keyword)
            )
        if status:
            queryset = queryset.filter(status=status)
        check_in_date = parse_date(request.query_params.get("check_in_date", ""))
        check_out_date = parse_date(request.query_params.get("check_out_date", ""))
        if check_in_date:
            queryset = queryset.filter(check_in_date=check_in_date)
        if check_out_date:
            queryset = queryset.filter(check_out_date=check_out_date)
        if ordering not in self._ORDERING_WHITELIST:
            ordering = "-id"
        queryset = queryset.order_by(ordering)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=BookingOrderSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)


class AdminOrdersDetailView(APIView):
    """管理员订单详情接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        order_id = request.query_params.get("order_id")
        if not order_id or not str(order_id).isdigit():
            return api_response(code=4002, message="缺少或无效的 order_id", data=None, status_code=400)
        order = BookingOrder.objects.filter(id=order_id).select_related("hotel", "room_type").prefetch_related("payments").first()
        if not order:
            return api_response(code=4040, message="订单不存在", data=None, status_code=404)
        payload = BookingOrderSerializer(order).data
        payload["payments"] = PaymentRecordSerializer(order.payments.order_by("-id"), many=True).data
        return api_response(data=payload)


class AdminOrdersChangeStatusView(APIView):
    """管理员订单状态流转接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = OrderStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        target_status = serializer.validated_data["target_status"]
        operator_remark = (serializer.validated_data.get("operator_remark", "") or "").strip()
        today = timezone.localdate()

        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(
                id=serializer.validated_data["order_id"]
            ).first()
            if not order:
                return api_response(code=4040, message="订单不存在", data=None, status_code=404)

            closed_statuses = {
                BookingOrder.STATUS_COMPLETED,
                BookingOrder.STATUS_CANCELLED,
                BookingOrder.STATUS_REFUNDED,
            }
            if order.status in closed_statuses and target_status != order.status:
                return api_response(code=4093, message="当前订单已关闭，无法再变更状态", data=None, status_code=409)
            if target_status == BookingOrder.STATUS_PENDING_PAYMENT:
                return api_response(code=4093, message="不支持手动回退为待支付状态", data=None, status_code=409)
            if target_status == BookingOrder.STATUS_CANCELLED and order.status in {BookingOrder.STATUS_CHECKED_IN, BookingOrder.STATUS_COMPLETED, BookingOrder.STATUS_CANCELLED, BookingOrder.STATUS_REFUNDED}:
                return api_response(code=4093, message="当前订单状态不允许取消", data=None, status_code=409)

            if target_status == BookingOrder.STATUS_CONFIRMED and order.status != BookingOrder.STATUS_PAID:
                return api_response(code=4093, message="仅已支付订单可确认", data=None, status_code=409)
            if target_status == BookingOrder.STATUS_CHECKED_IN:
                if order.status not in {BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED}:
                    return api_response(code=4093, message="当前订单状态不允许办理入住", data=None, status_code=409)
                if order.payment_status != BookingOrder.PAYMENT_PAID:
                    return api_response(code=4093, message="订单未支付，无法办理入住", data=None, status_code=409)
                if is_order_checkout_overdue(order, today=today):
                    return api_response(code=4093, message="订单已超过离店日期，无法办理入住，请人工核查", data=None, status_code=409)

            should_mark_direct_complete = False
            if target_status == BookingOrder.STATUS_COMPLETED:
                if order.status not in {BookingOrder.STATUS_CHECKED_IN, BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED}:
                    return api_response(code=4093, message="当前订单状态不允许直接完结", data=None, status_code=409)
                if order.payment_status != BookingOrder.PAYMENT_PAID:
                    return api_response(code=4093, message="订单未支付，无法完结", data=None, status_code=409)
                if order.status in {BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED}:
                    if not is_order_checkout_overdue(order, today=today):
                        return api_response(code=4093, message="未到离店日期，请先办理入住后再退房", data=None, status_code=409)
                    should_mark_direct_complete = True

            was_paid = order.payment_status == BookingOrder.PAYMENT_PAID
            order.status = target_status
            update_fields = ["status", "updated_at"]
            now = timezone.now()
            if target_status == BookingOrder.STATUS_PAID and not order.paid_at:
                order.paid_at = now
                update_fields.append("paid_at")
            if target_status == BookingOrder.STATUS_CONFIRMED and not order.confirmed_at:
                order.confirmed_at = now
                update_fields.append("confirmed_at")
            if target_status == BookingOrder.STATUS_CHECKED_IN and not order.checked_in_at:
                order.checked_in_at = now
                update_fields.append("checked_in_at")
            if target_status == BookingOrder.STATUS_COMPLETED and not order.completed_at:
                order.completed_at = now
                update_fields.append("completed_at")
            if target_status == BookingOrder.STATUS_CANCELLED and not order.cancelled_at:
                order.cancelled_at = now
                update_fields.append("cancelled_at")
            if target_status == BookingOrder.STATUS_CANCELLED and operator_remark:
                note = f"人工取消订单：{operator_remark}"
                if append_order_operator_remark(order, note):
                    update_fields.append("operator_remark")
            if should_mark_direct_complete:
                note = f"系统提示：离店日 {order.check_out_date} 已过，人工直接完结（未登记入住）"
                if append_order_operator_remark(order, note):
                    update_fields.append("operator_remark")

            # 管理员取消订单时归还库存、优惠券、处理退款
            if target_status == BookingOrder.STATUS_CANCELLED:
                nights = (order.check_out_date - order.check_in_date).days
                date_range = [order.check_in_date + timedelta(days=i) for i in range(nights)]
                RoomInventory.objects.filter(
                    room_type_id=order.room_type_id, date__in=date_range,
                ).update(stock=F("stock") + 1)
                if order.coupon_id:
                    UserCoupon.objects.filter(
                        pk=order.coupon_id,
                        status=UserCoupon.STATUS_USED,
                        used_order_id=order.id,
                    ).update(status=UserCoupon.STATUS_UNUSED, used_order=None, used_at=None)
                if was_paid:
                    order.payment_status = BookingOrder.PAYMENT_REFUNDED
                    update_fields.append("payment_status")
                    PaymentRecord.objects.filter(
                        order=order, status=PaymentRecord.STATUS_PAID,
                    ).update(status=PaymentRecord.STATUS_REFUNDED)
                    if order.points_earned > 0:
                        add_points(
                            order.user, -order.points_earned, PointsLog.TYPE_CONSUME_REWARD,
                            f"订单 {order.order_no} 管理员取消，回收消费积分",
                            order=order,
                        )
                        order.points_earned = 0
                        update_fields.append("points_earned")

            order.save(update_fields=update_fields)
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
                related_order=order,
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

        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(id=data["order_id"]).select_related("user").first()
            if not order:
                return api_response(code=4040, message="订单不存在", data=None, status_code=404)

            if order.status not in {BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED}:
                return api_response(code=4093, message="当前订单状态不允许办理入住", data=None, status_code=409)
            if order.payment_status != BookingOrder.PAYMENT_PAID:
                return api_response(code=4093, message="订单未支付，无法办理入住", data=None, status_code=409)
            if is_order_checkout_overdue(order):
                return api_response(code=4093, message="订单已超过离店日期，无法办理入住，请人工核查", data=None, status_code=409)

            # 房间号冲突检测：同酒店同时间段不允许重复入住
            room_no = data["room_no"]
            room_conflict = BookingOrder.objects.filter(
                hotel_id=order.hotel_id,
                room_no=room_no,
                status=BookingOrder.STATUS_CHECKED_IN,
                check_in_date__lt=order.check_out_date,
                check_out_date__gt=order.check_in_date,
            ).exclude(pk=order.pk).exists()
            if room_conflict:
                return api_response(code=4093, message=f"房间 {room_no} 在该日期范围内已被占用", data=None, status_code=409)

            order_remark = (data.get("operator_remark", "") or "").strip()
            order.status = BookingOrder.STATUS_CHECKED_IN
            if not order.checked_in_at:
                order.checked_in_at = timezone.now()
            order.room_no = room_no
            update_fields = ["status", "checked_in_at", "room_no", "updated_at"]
            if order_remark and append_order_operator_remark(order, order_remark):
                update_fields.append("operator_remark")
            order.save(update_fields=update_fields)
        SystemNotice.objects.create(
            user=order.user,
            notice_type=SystemNotice.TYPE_ORDER,
            title="已确认入住",
            content=f"订单 {order.order_no} 已办理入住，您的房间号为 {order.room_no}，祝您入住愉快！",
            related_order=order,
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

        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(id=data["order_id"]).select_related("user").first()
            if not order:
                return api_response(code=4040, message="订单不存在", data=None, status_code=404)

            if order.status in {
                BookingOrder.STATUS_COMPLETED,
                BookingOrder.STATUS_CANCELLED,
                BookingOrder.STATUS_REFUNDED,
                BookingOrder.STATUS_REFUNDING,
            }:
                return api_response(code=4093, message="当前订单状态不允许办理退房", data=None, status_code=409)
            if order.status not in {BookingOrder.STATUS_CHECKED_IN, BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED}:
                return api_response(code=4093, message="当前订单状态不允许办理退房", data=None, status_code=409)
            if order.payment_status != BookingOrder.PAYMENT_PAID:
                return api_response(code=4093, message="订单未支付，无法办理退房", data=None, status_code=409)

            overdue_without_checkin = order.status in {BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED}
            if overdue_without_checkin and not is_order_checkout_overdue(order):
                return api_response(code=4093, message="未到离店日期，请先办理入住", data=None, status_code=409)

            previous_status = order.status
            manual_remark = (data.get("operator_remark", "") or "").strip()
            update_fields = ["status", "completed_at", "updated_at"]
            order.status = BookingOrder.STATUS_COMPLETED
            if not order.completed_at:
                order.completed_at = timezone.now()
            remark_updated = False
            if manual_remark and append_order_operator_remark(order, manual_remark):
                remark_updated = True
            if overdue_without_checkin:
                note = f"系统提示：离店日 {order.check_out_date} 已过，补录退房（未登记入住）"
                if append_order_operator_remark(order, note):
                    remark_updated = True
            if remark_updated:
                update_fields.append("operator_remark")
            order.save(update_fields=update_fields)
        SystemNotice.objects.create(
            user=order.user,
            notice_type=SystemNotice.TYPE_ORDER,
            title="退房完成",
            content=f"订单 {order.order_no} 已办理退房，感谢您的入住，期待再次欢迎您！",
            related_order=order,
        )
        # 退房完成后奖励积分
        if previous_status == BookingOrder.STATUS_CHECKED_IN:
            add_points(order.user, 20, PointsLog.TYPE_CONSUME_REWARD, f"订单 {order.order_no} 入住奖励", order=order)
        return api_response(data={"order_id": order.id, "status": order.status})


class AdminOrdersExtendStayView(APIView):
    """续住办理接口：更新离店日期并写入操作备注。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = OrderExtendStaySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data

        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(id=data["order_id"]).select_related("user").first()
            if not order:
                return api_response(code=4040, message="订单不存在", data=None, status_code=404)

            if order.status in {
                BookingOrder.STATUS_COMPLETED,
                BookingOrder.STATUS_CANCELLED,
                BookingOrder.STATUS_REFUNDING,
                BookingOrder.STATUS_REFUNDED,
            }:
                return api_response(code=4093, message="当前订单状态不允许续住", data=None, status_code=409)
            if order.status not in {BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED, BookingOrder.STATUS_CHECKED_IN}:
                return api_response(code=4093, message="当前订单状态不允许续住", data=None, status_code=409)
            if order.payment_status != BookingOrder.PAYMENT_PAID:
                return api_response(code=4093, message="订单未支付，无法续住", data=None, status_code=409)

            new_check_out_date = data["new_check_out_date"]
            if new_check_out_date <= order.check_out_date:
                return api_response(code=4093, message="新的离店日期必须晚于当前离店日期", data=None, status_code=409)
            if new_check_out_date <= order.check_in_date:
                return api_response(code=4093, message="离店日期必须晚于入住日期", data=None, status_code=409)

            # 检查并扣减新增日期的库存
            extra_days = (new_check_out_date - order.check_out_date).days
            extra_date_range = [order.check_out_date + timedelta(days=i) for i in range(extra_days)]

            extra_inventories = list(
                RoomInventory.objects.select_for_update()
                .filter(room_type_id=order.room_type_id, date__in=extra_date_range, status="available")
            )
            inv_map = {inv.date: inv for inv in extra_inventories}
            for d in extra_date_range:
                inv = inv_map.get(d)
                if not inv or inv.stock <= 0:
                    return api_response(code=4003, message=f"{d} 库存不足，无法续住", data=None, status_code=400)
            for inv in extra_inventories:
                inv.stock -= 1
                inv.save(update_fields=["stock", "updated_at"])

            # 重新计算金额：新增天数按库存日价格累加
            extra_amount = sum(inv_map[d].price for d in extra_date_range)
            order.check_out_date = new_check_out_date
            order.original_amount = order.original_amount + extra_amount
            order.pay_amount = order.pay_amount + extra_amount
            update_fields = ["check_out_date", "original_amount", "pay_amount", "updated_at"]
            operator_remark = (data.get("operator_remark", "") or "").strip()
            base_note = f"续住办理：离店日期调整为 {new_check_out_date}，新增 {extra_days} 晚 ¥{extra_amount}"
            if operator_remark:
                base_note = f"{base_note}；备注：{operator_remark}"
            if append_order_operator_remark(order, base_note):
                update_fields.append("operator_remark")
            order.save(update_fields=update_fields)

        SystemNotice.objects.create(
            user=order.user,
            notice_type=SystemNotice.TYPE_ORDER,
            title="续住办理完成",
            content=f"订单 {order.order_no} 已完成续住，新的离店日期为 {new_check_out_date}，新增费用 ¥{extra_amount}。",
            related_order=order,
        )
        return api_response(
            data={
                "order_id": order.id,
                "check_out_date": order.check_out_date,
                "status": order.status,
            }
        )


class AdminOrdersSwitchRoomView(APIView):
    """换房办理接口：更新房间号并写入操作备注。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = OrderSwitchRoomSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data

        with transaction.atomic():
            order = BookingOrder.objects.select_for_update().filter(id=data["order_id"]).select_related("user").first()
            if not order:
                return api_response(code=4040, message="订单不存在", data=None, status_code=404)

            if order.status in {
                BookingOrder.STATUS_COMPLETED,
                BookingOrder.STATUS_CANCELLED,
                BookingOrder.STATUS_REFUNDING,
                BookingOrder.STATUS_REFUNDED,
            }:
                return api_response(code=4093, message="当前订单状态不允许换房", data=None, status_code=409)
            if order.status not in {BookingOrder.STATUS_PAID, BookingOrder.STATUS_CONFIRMED, BookingOrder.STATUS_CHECKED_IN}:
                return api_response(code=4093, message="当前订单状态不允许换房", data=None, status_code=409)
            if order.payment_status != BookingOrder.PAYMENT_PAID:
                return api_response(code=4093, message="订单未支付，无法换房", data=None, status_code=409)

            new_room_no = (data["new_room_no"] or "").strip()
            if not new_room_no:
                return api_response(code=4001, message="房间号不能为空", data=None, status_code=400)
            if order.room_no and order.room_no.strip() == new_room_no:
                return api_response(code=4093, message="新房间号与当前房间号一致", data=None, status_code=409)

            # 新房间号冲突检测
            room_conflict = BookingOrder.objects.filter(
                hotel_id=order.hotel_id,
                room_no=new_room_no,
                status=BookingOrder.STATUS_CHECKED_IN,
                check_in_date__lt=order.check_out_date,
                check_out_date__gt=order.check_in_date,
            ).exclude(pk=order.pk).exists()
            if room_conflict:
                return api_response(code=4093, message=f"房间 {new_room_no} 在该日期范围内已被占用", data=None, status_code=409)

            old_room_no = order.room_no or "未分配"
            order.room_no = new_room_no
            update_fields = ["room_no", "updated_at"]
            operator_remark = (data.get("operator_remark", "") or "").strip()
            base_note = f"换房办理：{old_room_no} -> {new_room_no}"
            if operator_remark:
                base_note = f"{base_note}；备注：{operator_remark}"
            if append_order_operator_remark(order, base_note):
                update_fields.append("operator_remark")
            order.save(update_fields=update_fields)

        SystemNotice.objects.create(
            user=order.user,
            notice_type=SystemNotice.TYPE_ORDER,
            title="换房办理完成",
            content=f"订单 {order.order_no} 已完成换房，当前房间号为 {order.room_no}。",
            related_order=order,
        )
        return api_response(
            data={
                "order_id": order.id,
                "room_no": order.room_no,
                "status": order.status,
            }
        )


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


class AdminReviewDeleteView(APIView):
    """管理员删除评价接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    def post(self, request):
        review_id = request.data.get("review_id")
        if not review_id:
            return api_response(code=4001, message="缺少 review_id 参数", data=None, status_code=400)
        deleted, _ = Review.objects.filter(id=review_id).delete()
        if not deleted:
            return api_response(code=4040, message="评价不存在", data=None, status_code=404)
        return api_response(data={"review_id": review_id, "deleted": True})


class AdminUsersView(APIView):
    """管理员用户列表接口。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    _ORDERING_WHITELIST = {
        "id", "-id",
        "user__username", "-user__username",
        "nickname", "-nickname",
        "mobile", "-mobile",
        "gender", "-gender",
        "role", "-role",
        "member_level", "-member_level",
        "points", "-points",
        "status", "-status",
        "created_at", "-created_at",
        "updated_at", "-updated_at",
    }

    def get(self, request):
        queryset = UserProfile.objects.select_related("user")
        keyword = request.query_params.get("keyword")
        ordering = request.query_params.get("ordering", "-id")
        if keyword:
            queryset = queryset.filter(Q(user__username__icontains=keyword) | Q(mobile__icontains=keyword) | Q(nickname__icontains=keyword))
        if ordering not in self._ORDERING_WHITELIST:
            ordering = "-id"
        queryset = queryset.order_by(ordering)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=UserProfileSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)


class AdminUsersChangeStatusView(APIView):
    """管理员用户状态修改接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

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
    """管理员员工管理接口：查询员工列表（hotel_admin 可操作），创建管理员账号（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    _ORDERING_WHITELIST = {
        "id", "-id",
        "user__username", "-user__username",
        "nickname", "-nickname",
        "mobile", "-mobile",
        "role", "-role",
        "status", "-status",
        "created_at", "-created_at",
        "updated_at", "-updated_at",
    }

    def get(self, request):
        queryset = UserProfile.objects.select_related("user").filter(role__in=[UserProfile.ROLE_HOTEL_ADMIN, UserProfile.ROLE_SYSTEM_ADMIN])
        ordering = request.query_params.get("ordering", "-id")
        if ordering not in self._ORDERING_WHITELIST:
            ordering = "-id"
        queryset = queryset.order_by(ordering)
        page, page_size = get_page_params(request)
        page_queryset, total = paginate_queryset(queryset, page, page_size)
        return paginated_response(items=UserProfileSerializer(page_queryset, many=True).data, page=page, page_size=page_size, total=total)

    def post(self, request):
        if get_user_role(request.user) != "system_admin":
            return api_response(code=4030, message="仅系统管理员可以创建员工账号", data=None, status_code=403)
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


class AdminEmployeeUpdateView(APIView):
    """管理员编辑员工接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    def post(self, request):
        serializer = EmployeeUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        profile = UserProfile.objects.filter(user_id=data["user_id"]).first()
        if not profile:
            return api_response(code=4040, message="员工不存在", data=None, status_code=404)
        if profile.role == UserProfile.ROLE_SYSTEM_ADMIN and "role" in data and data["role"] != UserProfile.ROLE_SYSTEM_ADMIN:
            return api_response(code=4030, message="不能修改系统管理员的角色", data=None, status_code=403)
        for field in ("nickname", "mobile", "role"):
            if field in data:
                setattr(profile, field, data[field])
        profile.save(update_fields=["nickname", "mobile", "role", "updated_at"])
        return api_response(data=UserProfileSerializer(profile).data)


class AdminEmployeeChangeStatusView(APIView):
    """管理员启用/禁用员工接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    def post(self, request):
        serializer = ChangeUserStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        profile = UserProfile.objects.filter(user_id=serializer.validated_data["user_id"]).first()
        if not profile:
            return api_response(code=4040, message="员工不存在", data=None, status_code=404)
        if profile.role == UserProfile.ROLE_SYSTEM_ADMIN:
            return api_response(code=4030, message="不能禁用系统管理员", data=None, status_code=403)
        profile.status = serializer.validated_data["status"]
        profile.save(update_fields=["status", "updated_at"])
        return api_response(data={"user_id": profile.user_id, "status": profile.status})


class AdminEmployeeResetPasswordView(APIView):
    """管理员重置员工密码接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    @staticmethod
    def _generate_password(length=12):
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        while True:
            pw = ''.join(secrets.choice(alphabet) for _ in range(length))
            if (any(c.islower() for c in pw) and any(c.isupper() for c in pw)
                    and any(c.isdigit() for c in pw)):
                return pw

    def post(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return api_response(code=4001, message="缺少 user_id 参数", data=None, status_code=400)
        profile = UserProfile.objects.select_related("user").filter(user_id=user_id).first()
        if not profile:
            return api_response(code=4040, message="员工不存在", data=None, status_code=404)
        if profile.role == UserProfile.ROLE_SYSTEM_ADMIN:
            return api_response(code=4030, message="不能重置系统管理员密码", data=None, status_code=403)
        new_password = self._generate_password()
        profile.user.set_password(new_password)
        profile.user.save(update_fields=["password"])
        _blacklist_user_tokens(profile.user)
        return api_response(data={"user_id": user_id, "new_password": new_password, "message": "密码已重置，请尽快通知用户修改"})


class AdminUserUpdateView(APIView):
    """管理端编辑用户信息接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    def post(self, request):
        serializer = AdminUserUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        profile = UserProfile.objects.filter(user_id=data["user_id"]).first()
        if not profile:
            return api_response(code=4040, message="用户不存在", data=None, status_code=404)
        for field in ("nickname", "mobile", "member_level"):
            if field in data:
                setattr(profile, field, data[field])
        profile.save(update_fields=["nickname", "mobile", "member_level", "updated_at"])
        return api_response(data=UserProfileSerializer(profile).data)


class AdminUserResetPasswordView(APIView):
    """管理端重置用户密码接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    def post(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return api_response(code=4001, message="缺少 user_id 参数", data=None, status_code=400)
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return api_response(code=4040, message="用户不存在", data=None, status_code=404)
        new_password = AdminEmployeeResetPasswordView._generate_password()
        user.set_password(new_password)
        user.save(update_fields=["password"])
        _blacklist_user_tokens(user)
        return api_response(data={"user_id": user_id, "new_password": new_password, "message": "密码已重置"})


class AdminSettingsView(APIView):
    """平台设置接口：读取（hotel_admin 可操作），更新（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    @staticmethod
    def _serialize_config(cfg: PlatformConfig) -> dict:
        return {
            "platform_name": cfg.platform_name,
            "admin_name": cfg.admin_name,
            "support_phone": cfg.support_phone,
            "support_email": cfg.support_email,
            "business_hours": cfg.business_hours,
            "platform_notice": cfg.platform_notice,
            "order_auto_cancel_minutes": cfg.order_auto_cancel_minutes,
        }

    def get(self, request):
        cfg = PlatformConfig.load()
        return api_response(data=self._serialize_config(cfg))

    def post(self, request):
        if get_user_role(request.user) != "system_admin":
            return api_response(code=4030, message="仅系统管理员可以修改平台设置", data=None, status_code=403)
        serializer = SettingsUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        cfg = PlatformConfig.load()
        data = serializer.validated_data
        for field in ("platform_name", "admin_name", "support_phone", "support_email", "business_hours", "platform_notice", "order_auto_cancel_minutes"):
            if field in data:
                setattr(cfg, field, data[field])
        cfg.save()
        return api_response(data=self._serialize_config(cfg))


class AdminSystemStatusView(APIView):
    """系统运行状态接口：CPU/内存/磁盘/数据库统计/服务连通性/进程运行时间。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    cache_key = "admin.system.status.v1"

    @staticmethod
    def _build_payload() -> dict:
        import os
        import platform
        import shutil
        import sys
        import time

        import django
        from django.db import connection

        process_start = time.time()

        uname = platform.uname()
        uptime_seconds = None
        if os.path.exists('/proc/uptime'):
            with open('/proc/uptime') as uptime_file:
                uptime_seconds = int(float(uptime_file.read().split()[0]))

        disk = shutil.disk_usage('/')
        disk_info = {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "usage_percent": round(disk.used / disk.total * 100, 1),
        }

        mem_info = None
        if os.path.exists('/proc/meminfo'):
            meminfo = {}
            with open('/proc/meminfo') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        meminfo[parts[0].rstrip(':')] = int(parts[1])
            total = meminfo.get('MemTotal', 0)
            available = meminfo.get('MemAvailable', 0)
            used = total - available
            mem_info = {
                "total_mb": round(total / 1024, 1),
                "used_mb": round(used / 1024, 1),
                "available_mb": round(available / 1024, 1),
                "usage_percent": round(used / total * 100, 1) if total else 0,
            }

        load_avg = None
        cpu_count = os.cpu_count() or 1
        if hasattr(os, 'getloadavg'):
            la = os.getloadavg()
            load_avg = {
                "1min": round(la[0], 2),
                "5min": round(la[1], 2),
                "15min": round(la[2], 2),
                "cores": cpu_count,
            }

        db_engine = connection.vendor
        db_name = connection.settings_dict.get('NAME', '')
        with connection.cursor() as cursor:
            db_stats = {"engine": db_engine, "name": db_name}
            if db_engine == 'sqlite':
                if db_name and os.path.exists(db_name):
                    db_stats["size_mb"] = round(os.path.getsize(db_name) / (1024 * 1024), 2)
            elif db_engine == 'postgresql':
                cursor.execute("SELECT pg_database_size(current_database())")
                db_stats["size_mb"] = round(cursor.fetchone()[0] / (1024 * 1024), 2)
            elif db_engine == 'mysql':
                cursor.execute(
                    "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) "
                    "FROM information_schema.tables WHERE table_schema = %s",
                    [db_name],
                )
                row = cursor.fetchone()
                if row and row[0]:
                    db_stats["size_mb"] = float(row[0])
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s",
                    [db_name],
                )
                db_stats["table_count"] = cursor.fetchone()[0]
            db_stats["host"] = connection.settings_dict.get('HOST', 'localhost') or 'localhost'
            db_stats["port"] = connection.settings_dict.get('PORT', '') or ''

        services = {}
        try:
            from django.conf import settings as django_settings
            broker_url = getattr(django_settings, 'CELERY_BROKER_URL', '')
            if broker_url:
                import redis
                r = redis.from_url(broker_url, socket_connect_timeout=0.8, socket_timeout=0.8)
                r.ping()
                redis_info = r.info('server')
                services["redis"] = {
                    "status": "connected",
                    "version": redis_info.get('redis_version', ''),
                    "url": broker_url.split('@')[-1] if '@' in broker_url else broker_url,
                }
        except Exception:
            services["redis"] = {"status": "disconnected"}

        try:
            from config.celery import app as celery_app
            insp = celery_app.control.inspect(timeout=1)
            active = insp.active()
            services["celery"] = {
                "status": "connected" if active is not None else "disconnected",
                "workers": len(active) if active else 0,
            }
        except Exception:
            services["celery"] = {"status": "disconnected", "workers": 0}

        User = get_user_model()
        biz_stats = {
            "users": User.objects.count(),
            "orders": BookingOrder.objects.count(),
            "hotels": Hotel.objects.count(),
            "room_types": RoomType.objects.count(),
            "reviews": Review.objects.count(),
            "notices": SystemNotice.objects.count(),
            "ai_calls": AICallLog.objects.count(),
        }

        elapsed_ms = round((time.time() - process_start) * 1000)
        return {
            "system": {
                "os": f"{uname.system} {uname.release}",
                "machine": uname.machine,
                "python": sys.version.split()[0],
                "django": django.__version__,
                "uptime_seconds": uptime_seconds,
            },
            "disk": disk_info,
            "memory": mem_info,
            "cpu_load": load_avg,
            "database": db_stats,
            "services": services,
            "business": biz_stats,
            "query_ms": elapsed_ms,
            "generated_at": timezone.now().isoformat(),
        }

    def get(self, request):
        force_refresh = str(request.query_params.get("refresh", "")).lower() in {"1", "true", "yes"}
        if not force_refresh:
            cached = cache.get(self.cache_key)
            if cached:
                return api_response(data={**cached, "cached": True})

        payload = self._build_payload()
        cache.set(self.cache_key, payload, 20)
        return api_response(data={**payload, "cached": False})


class AdminAISettingsView(APIView):
    """AI 设置接口：仅 system_admin 可查看或修改，避免供应商密钥外泄。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

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
        if get_user_role(request.user) != "system_admin":
            return api_response(code=4030, message="仅系统管理员可以修改 AI 配置", data=None, status_code=403)
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
    """新增或编辑 AI 供应商接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

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
    """切换活跃 AI 供应商接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

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
    """删除 AI 供应商接口（不允许删除当前活跃供应商，仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    def post(self, request):
        serializer = AIProviderDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        provider_name = serializer.validated_data["provider_name"]
        ai_settings = load_ai_settings()
        if provider_name == ai_settings.active_provider:
            return api_response(code=4093, message="不能删除当前活跃的供应商，请先切换到其他供应商", data=None, status_code=409)
        from config.ai import delete_ai_provider
        new_settings = delete_ai_provider(provider_name)
        return api_response(data={
            "providers": new_settings.list_providers(),
        })


class AdminAITestView(APIView):
    """管理员 AI 连通性测试接口：用于验证当前（或指定）供应商是否可用。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        serializer = AITestSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)

        data = serializer.validated_data
        provider_name = (data.get("provider_name") or "").strip() or None
        service = AIChatService(provider_name=provider_name)

        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="admin_ai_test",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(code=4001, message="当前 AI 供应商不可用或未配置", data=None, status_code=400)

        started_at = time.perf_counter()
        messages = [
            {
                "role": "system",
                "content": "你是酒店管理系统的 AI 连通性测试助手。请简洁回答，并包含“AI测试成功”四个字。",
            },
            {
                "role": "user",
                "content": data["message"],
            },
        ]
        try:
            result = service.create_chat_completion(messages, temperature=0)
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="admin_ai_test",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(
                data={
                    "scene": "admin_ai_test",
                    "provider": result.get("provider") or (service.provider.name if service.provider else ""),
                    "model": result.get("model") or (service.provider.chat_model if service.provider else ""),
                    "answer": (result.get("content") or "").strip(),
                    "latency_ms": latency_ms,
                }
            )
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="admin_ai_test",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
                latency_ms=int((time.perf_counter() - started_at) * 1000),
            )
            return api_response(code=5001, message="AI 测试调用失败，请检查供应商配置", data=None, status_code=500)


class AdminAIReportSummaryView(APIView):
    """AI 报表摘要接口：根据订单数据调用 LLM 生成运营总结文案。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        serializer = AIReportSummarySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="report_summary",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            orders = BookingOrder.objects.filter(
                check_in_date__gte=data["start_date"],
                check_out_date__lte=data["end_date"],
            )
            if data.get("hotel_id"):
                orders = orders.filter(hotel_id=data["hotel_id"])
            total_orders = orders.count()
            total_revenue = orders.filter(payment_status=BookingOrder.PAYMENT_PAID).aggregate(
                total=Sum("pay_amount")
            )["total"] or Decimal("0.00")
            summary = f"统计区间内共有 {total_orders} 笔订单，已支付营收 {total_revenue} 元。建议结合取消率与房型均价进一步分析。"
            return api_response(data={"scene": "report_summary", "summary": summary})
        try:
            started_at = time.perf_counter()
            result = service.generate_report_summary(
                hotel_id=data.get("hotel_id"),
                start_date=data["start_date"],
                end_date=data["end_date"],
            )
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="report_summary",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(data={"scene": "report_summary", "summary": result["summary"]})
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="report_summary",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={"scene": "report_summary", "summary": fallback_ai_reply("report_summary")})


class AdminAIReviewSummaryView(APIView):
    """AI 评价摘要接口：聚合评价区间数据并调用 LLM 输出洞察总结。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        serializer = AIReviewSummarySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="review_summary",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            reviews = Review.objects.filter(
                created_at__date__gte=data["start_date"],
                created_at__date__lte=data["end_date"],
            )
            if data.get("hotel_id"):
                reviews = reviews.filter(hotel_id=data["hotel_id"])
            avg_score = reviews.aggregate(avg=Avg("score"))["avg"] or 0
            summary = f"统计区间内共有 {reviews.count()} 条评价，平均评分 {round(avg_score, 2)} 分。建议重点关注低分评价中的重复问题。"
            return api_response(data={"scene": "review_summary", "summary": summary})
        try:
            started_at = time.perf_counter()
            result = service.generate_review_summary(
                hotel_id=data.get("hotel_id"),
                start_date=data["start_date"],
                end_date=data["end_date"],
            )
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="review_summary",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(data={"scene": "review_summary", "summary": result["summary"]})
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="review_summary",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={"scene": "review_summary", "summary": fallback_ai_reply("review_summary")})


class AdminAIReplySuggestionView(APIView):
    """AI 回复建议接口：基于评价内容调用 LLM 生成多风格客服回复建议。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        serializer = AIReplySuggestionSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        review = Review.objects.filter(id=serializer.validated_data["review_id"]).first()
        if not review:
            return api_response(code=4040, message="评价不存在", data=None, status_code=404)
        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="reply_suggestion",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(data={
                "scene": "reply_suggestion",
                "suggestions": [
                    {"style": "formal", "content": fallback_ai_reply("reply_suggestion")},
                ],
            })
        try:
            started_at = time.perf_counter()
            result = service.generate_reply_suggestion(review=review)
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="reply_suggestion",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(data={"scene": "reply_suggestion", "suggestions": result})
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="reply_suggestion",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={
                "scene": "reply_suggestion",
                "suggestions": [{"style": "formal", "content": fallback_ai_reply("reply_suggestion")}],
            })


class AdminReportTasksView(APIView):
    """报表任务接口：查询任务列表并创建示例报表任务。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    _ORDERING_WHITELIST = {
        "id", "-id",
        "report_type", "-report_type",
        "hotel__name", "-hotel__name",
        "start_date", "-start_date",
        "end_date", "-end_date",
        "status", "-status",
        "created_at", "-created_at",
        "updated_at", "-updated_at",
    }

    def get(self, request):
        queryset = ReportTask.objects.select_related("hotel")
        status = request.query_params.get("status")
        ordering = request.query_params.get("ordering", "-id")
        if status:
            queryset = queryset.filter(status=status)
        if ordering not in self._ORDERING_WHITELIST:
            ordering = "-id"
        queryset = queryset.order_by(ordering)
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


class AdminReportTaskDeleteView(APIView):
    """管理端删除报表任务接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    def post(self, request):
        task_id = request.data.get("task_id")
        if not task_id:
            return api_response(code=4001, message="缺少 task_id 参数", data=None, status_code=400)
        task = ReportTask.objects.filter(id=task_id).first()
        if not task:
            return api_response(code=4040, message="报表任务不存在", data=None, status_code=404)
        if task.status == ReportTask.STATUS_RUNNING:
            return api_response(code=4091, message="运行中的任务不可删除", data=None, status_code=409)
        task.delete()
        return api_response(data={"task_id": task_id, "deleted": True})


class AdminCouponTemplatesView(APIView):
    """管理端优惠券模板列表（hotel_admin 可操作），创建（仅 system_admin）。"""
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
        if get_user_role(request.user) != "system_admin":
            return api_response(code=4030, message="仅系统管理员可以创建优惠券模板", data=None, status_code=403)
        serializer = CouponTemplateCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        tpl = CouponTemplate.objects.create(**serializer.validated_data)
        return api_response(data=CouponTemplateSerializer(tpl).data)


class AdminCouponTemplateUpdateView(APIView):
    """管理端优惠券模板编辑接口（仅 system_admin）：支持全字段编辑及上/下架。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    def post(self, request):
        serializer = CouponTemplateEditSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        tpl = CouponTemplate.objects.filter(id=data["template_id"]).first()
        if not tpl:
            return api_response(code=4040, message="模板不存在", data=None, status_code=404)
        update_fields = ["updated_at"]
        for field in ("name", "coupon_type", "amount", "discount", "min_amount", "total_count",
                       "per_user_limit", "required_level", "points_cost", "valid_days",
                       "valid_start", "valid_end", "status"):
            if field in data:
                setattr(tpl, field, data[field])
                update_fields.append(field)
        tpl.save(update_fields=update_fields)
        return api_response(data=CouponTemplateSerializer(tpl).data)


class AdminCouponTemplateDeleteView(APIView):
    """管理端优惠券模板删除接口（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    def post(self, request):
        tpl_id = request.data.get("template_id")
        if not tpl_id:
            return api_response(code=4001, message="缺少 template_id 参数", data=None, status_code=400)
        tpl = CouponTemplate.objects.filter(id=tpl_id).first()
        if not tpl:
            return api_response(code=4040, message="模板不存在", data=None, status_code=404)
        if tpl.claimed_count > 0:
            return api_response(code=4091, message="该模板已有用户领取，无法删除，请改为下架", data=None, status_code=409)
        tpl.delete()
        return api_response(data={"template_id": tpl_id, "deleted": True})


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
    """系统重置接口：清除所有业务数据，恢复到初始状态（仅 system_admin）。"""
    permission_classes = [IsAuthenticated, IsSystemAdminRole]

    def post(self, request):
        serializer = SystemResetSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="请输入 RESET 确认重置", data={"errors": serializer.errors}, status_code=400)

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


# ──────────────────────────────────────────────────────────────────────────────
# 新增 AI 功能视图 §15 — 管理员 AI 增强接口
# ──────────────────────────────────────────────────────────────────────────────

class AdminAIPricingSuggestionView(APIView):
    """AI 智能定价建议接口：基于房型与历史数据生成价格优化建议。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        serializer = AIPricingSuggestionSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        room_type = RoomType.objects.filter(id=data["room_type_id"]).first()
        if not room_type:
            return api_response(code=4040, message="房型不存在", data=None, status_code=404)
        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="pricing_suggestion",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(data={"scene": "pricing_suggestion", "suggestions": [], "message": fallback_ai_reply("pricing_suggestion")})
        try:
            started_at = time.perf_counter()
            result = service.generate_pricing_suggestion(
                room_type=room_type,
                target_dates=data["target_dates"],
                use_reasoning=data.get("use_reasoning", False),
            )
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="pricing_suggestion",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(data={"scene": "pricing_suggestion", "suggestions": result["suggestions"], "overall_analysis": result.get("overall_analysis", "")})
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="pricing_suggestion",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={"scene": "pricing_suggestion", "suggestions": [], "message": fallback_ai_reply("pricing_suggestion")})


class AdminAIBusinessReportView(APIView):
    """AI 深度经营报告接口：生成多维度经营分析 Markdown 报告。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        serializer = AIBusinessReportSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="business_report",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(data={"scene": "business_report", "report": fallback_ai_reply("business_report")})
        try:
            started_at = time.perf_counter()
            result = service.generate_business_report(
                hotel_id=data.get("hotel_id"),
                start_date=data["start_date"],
                end_date=data["end_date"],
                dimensions=data.get("dimensions"),
                use_reasoning=data.get("use_reasoning", False),
            )
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="business_report",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(data={"scene": "business_report", "report": result.get("report_markdown", "")})
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="business_report",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={"scene": "business_report", "report": fallback_ai_reply("business_report")})


class AdminAIBusinessReportStreamView(APIView):
    """AI 深度经营报告流式接口：SSE 格式逐 token 推送 Markdown 报告内容。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        import json
        from django.http import StreamingHttpResponse

        serializer = AIBusinessReportSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        started_at = time.perf_counter()

        def event_stream():
            if not service.is_available():
                record_ai_call_log(
                    user=request.user,
                    scene="business_report",
                    service=service,
                    status=AICallLog.STATUS_FAILED,
                    error_message="AI service unavailable",
                )
                fallback = fallback_ai_reply("business_report")
                yield f"data: {json.dumps({'type': 'chunk', 'content': fallback, 'done': False}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'content': '', 'done': True})}\n\n"
                return
            try:
                stream_result = service.stream_business_report(
                    hotel_id=data.get("hotel_id"),
                    start_date=data["start_date"],
                    end_date=data["end_date"],
                    dimensions=data.get("dimensions"),
                    use_reasoning=data.get("use_reasoning", False),
                )
                # stream_business_report returns (text, None) tuple on fallback or an OpenAI stream
                if isinstance(stream_result, tuple):
                    text, _ = stream_result
                    record_ai_call_log(
                        user=request.user,
                        scene="business_report",
                        service=service,
                        status=AICallLog.STATUS_FAILED,
                        error_message="AI stream fallback response",
                        latency_ms=int((time.perf_counter() - started_at) * 1000),
                    )
                    yield f"data: {json.dumps({'type': 'chunk', 'content': text, 'done': False}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'content': '', 'done': True})}\n\n"
                    return

                record_ai_call_log(
                    user=request.user,
                    scene="business_report",
                    service=service,
                    status=AICallLog.STATUS_SUCCESS,
                    latency_ms=int((time.perf_counter() - started_at) * 1000),
                )
                for chunk in stream_result:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    token = (delta.content or "") if delta else ""
                    done = (chunk.choices[0].finish_reason is not None) if chunk.choices else False
                    event_type = "done" if done else "chunk"
                    yield f"data: {json.dumps({'type': event_type, 'content': token, 'done': done}, ensure_ascii=False)}\n\n"
            except Exception as exc:
                record_ai_call_log(
                    user=request.user,
                    scene="business_report",
                    service=service,
                    status=AICallLog.STATUS_FAILED,
                    error_message=str(exc),
                    latency_ms=int((time.perf_counter() - started_at) * 1000),
                )
                fallback = fallback_ai_reply("business_report")
                yield f"data: {json.dumps({'type': 'chunk', 'content': fallback, 'done': False}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'content': '', 'done': True})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class AdminAIReviewSentimentView(APIView):
    """AI 评价情感分析接口：分析单条评价的情感倾向并保存分析结果。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        from django.utils import timezone as tz

        serializer = AIReviewSentimentSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        review = Review.objects.filter(id=serializer.validated_data["review_id"]).first()
        if not review:
            return api_response(code=4040, message="评价不存在", data=None, status_code=404)
        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="review_sentiment",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(data={"scene": "review_sentiment", "result": None, "message": fallback_ai_reply("review_sentiment")})
        try:
            started_at = time.perf_counter()
            result = service.analyze_review_sentiment(review=review)
            # 将情感分析结果持久化到 Review 模型
            Review.objects.filter(id=review.id).update(
                sentiment_score=result.get("sentiment_score"),
                sentiment_label=result.get("sentiment_label", ""),
                auto_tags=result.get("tags", []),
                sentiment_keywords=result.get("keywords", []),
                sentiment_analyzed_at=tz.now(),
            )
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="review_sentiment",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            # 转换字段名以匹配前端期望的格式
            return api_response(data={"scene": "review_sentiment", "result": {
                "score": result.get("sentiment_score", 0),
                "label": result.get("sentiment_label", "neutral"),
                "keywords": result.get("keywords", []),
                "tags": result.get("tags", []),
                "summary": result.get("summary", ""),
            }})
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="review_sentiment",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={"scene": "review_sentiment", "result": None, "message": fallback_ai_reply("review_sentiment")})


class AdminAIMarketingCopyView(APIView):
    """AI 营销文案生成接口：根据酒店信息与活动类型生成多风格营销文案。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        serializer = AIMarketingCopySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="marketing_copy",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(data={"scene": "marketing_copy", "copies": [], "message": fallback_ai_reply("marketing_copy")})
        try:
            started_at = time.perf_counter()
            result = service.generate_marketing_copy(
                hotel_id=data.get("hotel_id"),
                copy_type=data["copy_type"],
                style=data.get("style", "formal"),
                keywords=data.get("keywords", []),
                target_audience=data.get("target_audience", ""),
                extra_notes=data.get("extra_notes", ""),
            )
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="marketing_copy",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(data={"scene": "marketing_copy", "copies": result.get("copies", [])})
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="marketing_copy",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={"scene": "marketing_copy", "copies": [], "message": fallback_ai_reply("marketing_copy")})


class AdminAIContentGenerateView(APIView):
    """AI 内容生成接口：生成酒店介绍、房型描述或 SEO 关键词候选内容。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        serializer = AIContentGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="content_generate",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(data={"scene": "content_generate", "results": [], "message": fallback_ai_reply("content_generate")})
        try:
            started_at = time.perf_counter()
            result = service.generate_content(
                content_type=data["content_type"],
                context_data=data["context"],
                count=data.get("count", 3),
            )
            # 标准化 candidates 为 {content, highlights} 对象列表
            raw_candidates = result.get("candidates", [])
            results = []
            for c in raw_candidates:
                if isinstance(c, dict):
                    results.append({"content": c.get("content", str(c)), "highlights": c.get("highlights", [])})
                else:
                    results.append({"content": str(c), "highlights": []})
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="content_generate",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(data={"scene": "content_generate", "results": results})
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="content_generate",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={"scene": "content_generate", "results": [], "message": fallback_ai_reply("content_generate")})


class AdminAIAnomalyReportView(APIView):
    """AI 异常检测报告接口：检测酒店经营数据中的异常信号。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        serializer = AIAnomalyReportSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="anomaly_report",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(data={"scene": "anomaly_report", "anomalies": [], "message": fallback_ai_reply("anomaly_report")})
        try:
            started_at = time.perf_counter()
            result = service.generate_anomaly_report(
                hotel_id=data.get("hotel_id"),
                analysis_date=data.get("date"),
            )
            # 展开 result 并转换字段名以匹配前端
            severity_map = {"danger": "high", "warning": "medium", "info": "low"}
            anomalies = []
            for a in result.get("anomalies", []):
                anomalies.append({
                    "type": a.get("type", ""),
                    "level": severity_map.get(a.get("severity", "info"), "low"),
                    "description": a.get("description", a.get("ai_analysis", "")),
                })
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="anomaly_report",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(data={
                "scene": "anomaly_report",
                "anomalies": anomalies,
                "summary": result.get("overall_status", ""),
            })
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="anomaly_report",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={"scene": "anomaly_report", "anomalies": [], "summary": "", "message": fallback_ai_reply("anomaly_report")})


class AdminAIOrderAnomalySummaryView(APIView):
    """AI 订单异常摘要接口：检测逾期未付、异常取消等订单风险。"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def post(self, request):
        serializer = AIOrderAnomalySummarySerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="order_anomaly",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(data={"scene": "order_anomaly", "anomalies": [], "summary": fallback_ai_reply("anomaly_report")})
        try:
            started_at = time.perf_counter()
            result = service.generate_order_anomaly_summary(analysis_date=data.get("date"))
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="order_anomaly",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(data={
                "scene": "order_anomaly",
                "anomalies": result.get("anomalies", []),
                "summary": result.get("summary", ""),
            })
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="order_anomaly",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={"scene": "order_anomaly", "anomalies": [], "summary": fallback_ai_reply("anomaly_report")})


class AdminAICallLogsView(APIView):
    """AI 调用日志查询接口：分页查询 AI 调用历史记录。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = AICallLog.objects.select_related("user").order_by("-created_at")
        scene = request.query_params.get("scene")
        status = request.query_params.get("status")
        if scene:
            queryset = queryset.filter(scene=scene)
        if status:
            queryset = queryset.filter(status=status)
        page, page_size = get_page_params(request)
        page_qs, total = paginate_queryset(queryset, page, page_size)
        items = AICallLogSerializer(page_qs, many=True).data
        return paginated_response(items=items, page=page, page_size=page_size, total=total)


class AdminAIUsageStatsView(APIView):
    """AI 用量统计接口：按场景 / 状态汇总 token 用量与费用估算。"""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        from django.db.models import Count

        queryset = AICallLog.objects.all()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        success_count = queryset.filter(status="success").count()
        failed_count = queryset.filter(status__in=["failed", "timeout", "quota_exceeded"]).count()

        by_scene_qs = queryset.values("scene").annotate(calls=Count("id"))
        by_scene = {item["scene"]: item["calls"] for item in by_scene_qs}

        by_provider_qs = queryset.values("provider").annotate(calls=Count("id"))
        by_provider = {item["provider"]: item["calls"] for item in by_provider_qs}

        totals = queryset.aggregate(
            total_calls=Count("id"),
            total_tokens=Sum("total_tokens"),
            total_cost=Sum("cost_estimate"),
        )
        return api_response(data={
            "total_calls": totals["total_calls"] or 0,
            "success_calls": success_count,
            "failed_calls": failed_count,
            "total_tokens": totals["total_tokens"] or 0,
            "total_cost": float(totals["total_cost"] or 0),
            "by_scene": by_scene,
            "by_provider": by_provider,
        })


# ──────────────────────────────────────────────────────────────────────────────
# 新增 AI 功能视图 §15 — 用户端 AI 接口
# ──────────────────────────────────────────────────────────────────────────────

class UserAIRecommendationsView(APIView):
    """用户 AI 推荐接口：基于用户偏好和当前场景返回个性化推荐酒店列表。"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_user"

    def post(self, request):
        serializer = AIRecommendationsSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        data = serializer.validated_data
        limit = data.get("limit", 6)

        def _fallback():
            hotels = Hotel.objects.filter(status=Hotel.STATUS_ONLINE).order_by("-created_at")[:limit]
            return [
                {
                    "id": h.id, "name": h.name, "city": h.city, "star": h.star,
                    "min_price": float(h.min_price), "cover_image": h.cover_image or "",
                    "rating": float(h.rating), "reason": "",
                }
                for h in hotels
            ]

        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="recommendations",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(data={"scene": "recommendations", "recommendations": _fallback()})
        try:
            started_at = time.perf_counter()
            raw_recs = service.generate_recommendations(
                user=request.user,
                scene=data.get("scene", "home"),
                hotel_id=data.get("hotel_id"),
                keyword=data.get("keyword", ""),
                limit=limit,
            )
            # 将服务层字段名映射为前端期望的格式
            recommendations = [
                {
                    "id": rec.get("hotel_id"),
                    "name": rec.get("hotel_name"),
                    "city": rec.get("city"),
                    "star": rec.get("star"),
                    "min_price": rec.get("min_price"),
                    "cover_image": rec.get("cover_image", ""),
                    "rating": rec.get("rating"),
                    "reason": rec.get("recommendation_reason", ""),
                }
                for rec in raw_recs
            ]
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="recommendations",
                service=service,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )
            return api_response(data={"scene": "recommendations", "recommendations": recommendations})
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="recommendations",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            return api_response(data={"scene": "recommendations", "recommendations": _fallback()})


class UserAIHotelCompareView(APIView):
    """用户 AI 对比接口：对 2-3 家酒店进行多维度智能对比分析。"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_user"

    def _serialize_hotels(self, hotels):
        serialized = []
        for hotel in hotels:
            room_types = list(
                hotel.room_types.filter(status=RoomType.STATUS_ONLINE).order_by("base_price")[:3]
            )
            serialized.append({
                "id": hotel.id,
                "name": hotel.name,
                "city": hotel.city,
                "star": hotel.star,
                "rating": float(hotel.rating),
                "min_price": float(hotel.min_price),
                "address": hotel.address,
                "description": (hotel.description or "")[:200],
                "room_types": [
                    {
                        "name": room.name,
                        "bed_type": room.get_bed_type_display(),
                        "area": room.area,
                        "price": float(room.base_price),
                    }
                    for room in room_types
                ],
            })
        return serialized

    def _build_fallback_result(self, hotels, recommendation: str):
        return {
            "scene": "hotel_compare",
            "hotels": self._serialize_hotels(hotels),
            "comparison": None,
            "ai_summary": "",
            "recommendation": recommendation,
            "dimensions": [],
            "winner_id": None,
            "winner_reason": "",
            "ai_generated": False,
        }

    def post(self, request):
        serializer = AIHotelCompareSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)

        data = serializer.validated_data
        hotel_ids = data["hotel_ids"]

        hotels_by_id = {
            hotel.id: hotel
            for hotel in Hotel.objects.filter(
                id__in=hotel_ids, status=Hotel.STATUS_ONLINE
            ).prefetch_related("room_types")
        }
        hotels = [hotels_by_id[hid] for hid in hotel_ids if hid in hotels_by_id]
        if len(hotels) < 2:
            return api_response(
                code=4001,
                message="可对比酒店不足，只有上架酒店可参与对比",
                data={"errors": {"hotel_ids": ["至少需要 2 家上架酒店"]}},
                status_code=400,
            )

        service = AIChatService()
        if not service.is_available():
            record_ai_call_log(
                user=request.user,
                scene="hotel_compare",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message="AI service unavailable",
            )
            return api_response(data=self._build_fallback_result(hotels, fallback_ai_reply("hotel_compare")))

        try:
            started_at = time.perf_counter()
            result = service.generate_hotel_compare(
                hotel_ids=[hotel.id for hotel in hotels],
                check_in_date=data.get("check_in_date"),
                check_out_date=data.get("check_out_date"),
            )
            serialized_hotels = result.get("hotels") if isinstance(result.get("hotels"), list) else []
            if not serialized_hotels:
                serialized_hotels = self._serialize_hotels(hotels)

            latency_ms = int((time.perf_counter() - started_at) * 1000)
            record_ai_call_log(
                user=request.user,
                scene="hotel_compare",
                service=service,
                result=result,
                status=AICallLog.STATUS_SUCCESS,
                latency_ms=latency_ms,
            )

            return api_response(data={
                "scene": "hotel_compare",
                "hotels": serialized_hotels,
                "comparison": result.get("comparison"),
                "ai_summary": result.get("ai_summary", ""),
                "recommendation": result.get("recommendation") or fallback_ai_reply("hotel_compare"),
                "dimensions": result.get("dimensions", []),
                "winner_id": result.get("winner_id"),
                "winner_reason": result.get("winner_reason", ""),
                "ai_generated": result.get("ai_generated", False),
            })
        except Exception as exc:
            record_ai_call_log(
                user=request.user,
                scene="hotel_compare",
                service=service,
                status=AICallLog.STATUS_FAILED,
                error_message=str(exc),
            )
            logger.exception("AI 酒店对比失败，hotel_ids=%s", hotel_ids)
            return api_response(data=self._build_fallback_result(hotels, fallback_ai_reply("hotel_compare")))


class UserAISessionsView(APIView):
    """用户 AI 会话列表接口：查询当前用户的 AI 对话会话列表，支持删除会话。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user).order_by("-last_message_at")
        page, page_size = get_page_params(request)
        page_sessions, total = paginate_queryset(sessions, page, page_size)
        items = ChatSessionSerializer(page_sessions, many=True).data
        return paginated_response(items=items, page=page, page_size=page_size, total=total)

    def post(self, request):
        """通过 action 字段处理写操作（目前支持 action=delete）。"""
        if request.data.get("action") != "delete":
            return api_response(code=4001, message="不支持的操作", data=None, status_code=400)
        serializer = ChatSessionDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(code=4001, message="参数错误", data={"errors": serializer.errors}, status_code=400)
        session = ChatSession.objects.filter(id=serializer.validated_data["session_id"], user=request.user).first()
        if not session:
            return api_response(code=4040, message="会话不存在", data=None, status_code=404)
        session.delete()
        return api_response(data={"deleted": True})


class UserAISessionMessagesView(APIView):
    """用户 AI 会话消息接口：查询指定会话的消息历史。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id: int):
        session = ChatSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return api_response(code=4040, message="会话不存在", data=None, status_code=404)
        messages = ChatMessage.objects.filter(session=session).order_by("created_at")
        page, page_size = get_page_params(request)
        page_messages, total = paginate_queryset(messages, page, page_size)
        items = ChatMessageSerializer(page_messages, many=True).data
        return paginated_response(items=items, page=page, page_size=page_size, total=total)

