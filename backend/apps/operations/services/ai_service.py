"""apps/operations/services/ai_service.py —— AI 对话服务封装（多模型支持）。"""

from __future__ import annotations

import json
import logging
import math
import re
from collections.abc import Iterator
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.utils import timezone

from apps.bookings.models import BookingOrder
from apps.crm.models import Review
from apps.hotels.models import Hotel, RoomType
from apps.operations.models import SystemNotice
from apps.operations.services.prompt_service import PromptSceneError, PromptTemplateService, SUPPORTED_CUSTOMER_SERVICE_TOPICS
from config.ai import AIProviderConfig, build_ai_client, load_ai_settings

logger = logging.getLogger(__name__)


class AIChatService:
    """AI 对话服务封装，支持多供应商切换、提示词渲染与上下文绑定。"""

    USER_CHAT_SCENE_ALIASES = {
        "customer_service": "customer_service",
        "booking_assistant": "booking_assistant",
        "general": "general",
    }

    BOOKING_INTENT_KEYWORDS = (
        "订酒店",
        "想订",
        "选酒店",
        "找酒店",
        "预订",
        "订房",
        "订个房",
        "住酒店",
        "入住",
        "房型",
        "客房",
        "开房",
        "住哪",
    )
    BOOKING_RESET_KEYWORDS = ("重新订", "重选", "换个城市", "重新开始", "重新选", "重来")
    BOOKING_SWITCH_HOTEL_KEYWORDS = ("换一家", "换个酒店", "换酒店", "不要这个", "别家", "换别的酒店")
    BOOKING_CHEAP_KEYWORDS = ("便宜", "最便宜", "性价比", "划算", "省钱", "低价")
    BOOKING_HIGH_RATING_KEYWORDS = ("高评分", "评分高", "评价好", "口碑好", "五星", "高星")
    BOOKING_CENTER_KEYWORDS = ("市中心", "中心", "商圈", "地铁", "交通方便", "近地铁")
    BOOKING_FAMILY_KEYWORDS = ("亲子", "家庭", "带娃", "儿童", "一家人")
    BOOKING_BUSINESS_KEYWORDS = ("出差", "商务", "商旅", "开会")
    BOOKING_NEARBY_KEYWORDS = ("附近", "最近", "离", "周边")
    CUSTOMER_SERVICE_KEYWORDS = (
        "订单",
        "取消",
        "退款",
        "支付",
        "发票",
        "会员",
        "积分",
        "通知",
        "改期",
        "改签",
        "入住",
        "离店",
    )
    POI_CANDIDATES = (
        {"name": "西湖", "city": "杭州", "lat": 30.243060, "lng": 120.150818, "aliases": ["西湖", "杭州西湖"]},
        {"name": "天安门", "city": "北京", "lat": 39.908722, "lng": 116.397499, "aliases": ["天安门"]},
        {"name": "外滩", "city": "上海", "lat": 31.240000, "lng": 121.490000, "aliases": ["外滩", "上海外滩"]},
        {"name": "广州塔", "city": "广州", "lat": 23.108500, "lng": 113.324500, "aliases": ["广州塔", "小蛮腰"]},
        {"name": "深圳湾公园", "city": "深圳", "lat": 22.506000, "lng": 113.935000, "aliases": ["深圳湾", "深圳湾公园"]},
    )

    def __init__(self, provider_name: str | None = None) -> None:
        self.settings = load_ai_settings()
        if provider_name:
            self._provider = self.settings.get_provider(provider_name)
        else:
            self._provider = self.settings.get_active_provider()
        self.prompt_service = PromptTemplateService()

    @property
    def provider(self) -> AIProviderConfig | None:
        return self._provider

    def is_available(self) -> bool:
        return self.settings.enabled and self._provider is not None and self._provider.is_configured

    def normalize_scene(self, scene: str) -> str:
        return self._normalize_requested_scene(scene)

    def _normalize_requested_scene(self, scene: str) -> str:
        raw = (scene or "").strip().lower()
        normalized = self.USER_CHAT_SCENE_ALIASES.get(raw)
        if not normalized:
            raise PromptSceneError(f"unsupported AI scene: {scene}")
        return normalized

    def _resolve_chat_mode(
        self,
        *,
        requested_scene: str,
        question: str,
        hotel_id: int | None,
        booking_context: dict[str, Any] | None,
    ) -> str:
        if requested_scene == "customer_service":
            return "customer_service"
        if requested_scene == "booking_assistant":
            return "booking_assistant"
        if any(keyword in question for keyword in self.CUSTOMER_SERVICE_KEYWORDS):
            return "customer_service"
        normalized_context = self._normalize_booking_context(booking_context)
        if self._should_enter_booking_flow(
            question,
            hotel_id=hotel_id,
            booking_context=normalized_context,
            force_booking_flow=False,
        ):
            return "booking_assistant"
        return "customer_service"

    def reply_customer_service(
        self,
        *,
        user: Any,
        scene: str,
        question: str,
        hotel_id: int | None = None,
        order_id: int | None = None,
        booking_context: dict[str, Any] | None = None,
        conversation_summary: str = "",
    ) -> dict[str, Any]:
        requested_scene = self._normalize_requested_scene(scene)
        chat_mode = self._resolve_chat_mode(
            requested_scene=requested_scene,
            question=question,
            hotel_id=hotel_id,
            booking_context=booking_context,
        )
        booking_assistant = None
        allow_booking_assistant = chat_mode == "booking_assistant"

        if allow_booking_assistant:
            booking_assistant = self._build_booking_assistant_response(
                user=user,
                question=question,
                requested_scene=requested_scene,
                hotel_id=hotel_id,
                booking_context=booking_context,
            )
            if booking_assistant is not None:
                return {
                    "scene": chat_mode,
                    "answer": booking_assistant["answer"],
                    "booking_assistant": booking_assistant,
                }

        if chat_mode == "customer_service":
            booking_assistant = self._build_customer_service_action_response(
                user=user,
                order_id=order_id,
                question=question,
            )

        if chat_mode == "booking_assistant":
            _, messages = self.build_booking_assistant_messages(
                user=user,
                scene=chat_mode,
                question=question,
                hotel_id=hotel_id,
                booking_context=booking_context,
                conversation_summary=conversation_summary,
            )
        else:
            _, messages = self.build_customer_service_messages(
                user=user,
                scene=chat_mode,
                question=question,
                hotel_id=hotel_id,
                order_id=order_id,
                conversation_summary=conversation_summary,
            )

        try:
            if self.is_available():
                result = self.create_chat_completion(messages, temperature=0.2)
                answer = result["content"]
            else:
                answer = ""
        except Exception:
            logger.exception("AI chat reply fallback triggered")
            answer = ""

        return {
            "scene": chat_mode,
            "answer": answer,
            "booking_assistant": booking_assistant,
        }

    def iter_text_chunks(self, text: str, chunk_size: int = 24) -> Iterator[str]:
        if not text:
            return
        start = 0
        while start < len(text):
            yield text[start:start + chunk_size]
            start += chunk_size

    def build_customer_service_messages(
        self,
        *,
        user: Any,
        scene: str,
        question: str,
        hotel_id: int | None = None,
        order_id: int | None = None,
        conversation_summary: str = "",
    ) -> tuple[str, list[dict[str, str]]]:
        if scene != "customer_service":
            raise PromptSceneError(f"unsupported AI scene: {scene}")

        prompt_context = self._build_customer_service_prompt_context(
            user=user,
            hotel_id=hotel_id,
            order_id=order_id,
            conversation_summary=conversation_summary,
        )
        messages = [
            {
                "role": "system",
                "content": self.prompt_service.render("customer_service/system.j2", **prompt_context),
            },
            {
                "role": "user",
                "content": self.prompt_service.render("customer_service/user.j2", question=question),
            },
        ]
        return scene, messages

    def build_booking_assistant_messages(
        self,
        *,
        user: Any,
        scene: str,
        question: str,
        hotel_id: int | None = None,
        booking_context: dict[str, Any] | None = None,
        conversation_summary: str = "",
    ) -> tuple[str, list[dict[str, str]]]:
        if scene != "booking_assistant":
            raise PromptSceneError(f"unsupported AI scene: {scene}")

        prompt_context = self._build_booking_assistant_prompt_context(
            user=user,
            question=question,
            hotel_id=hotel_id,
            booking_context=booking_context,
            conversation_summary=conversation_summary,
        )
        messages = [
            {
                "role": "system",
                "content": self.prompt_service.render("booking_assistant/system.j2", **prompt_context),
            },
            {
                "role": "user",
                "content": self.prompt_service.render("booking_assistant/user.j2", **prompt_context),
            },
        ]
        return scene, messages

    def create_chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        if not self.is_available():
            raise RuntimeError("AI service is not configured. Check AI_ENABLED and provider API keys.")

        client = build_ai_client(self._provider)
        use_model = model or (self._provider.chat_model if self._provider else "")
        response = client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=temperature,
        )
        content = ""
        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content or ""

        return {
            "provider": self._provider.name if self._provider else "",
            "model": response.model,
            "content": content,
            "raw": response.model_dump(),
        }

    def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> Any:
        if not self.is_available():
            raise RuntimeError("AI service is not configured. Check AI_ENABLED and provider API keys.")

        client = build_ai_client(self._provider)
        use_model = model or (self._provider.chat_model if self._provider else "")
        return client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )

    def _build_customer_service_prompt_context(
        self,
        *,
        user: Any,
        hotel_id: int | None,
        order_id: int | None,
        conversation_summary: str,
    ) -> dict[str, Any]:
        user_orders = BookingOrder.objects.filter(user=user).select_related("hotel", "room_type")
        requested_order = user_orders.filter(id=order_id).first() if order_id else None

        requested_hotel = None
        if requested_order is not None:
            requested_hotel = requested_order.hotel
        elif hotel_id:
            requested_hotel = Hotel.objects.filter(id=hotel_id, status=Hotel.STATUS_ONLINE).first()

        room_types = []
        if requested_hotel is not None:
            room_types = [
                self._serialize_room_type(item)
                for item in RoomType.objects.filter(hotel=requested_hotel, status=RoomType.STATUS_ONLINE).order_by("id")[:10]
            ]

        recent_order_models = list(user_orders[:5])
        recent_orders = [self._serialize_order(item) for item in recent_order_models]
        recommended_hotels = [
            self._serialize_hotel(item)
            for item in Hotel.objects.filter(status=Hotel.STATUS_ONLINE, is_recommended=True).order_by("-updated_at", "-id")[:5]
        ]
        recent_notices = [
            self._serialize_notice(item)
            for item in SystemNotice.objects.filter(user=user).order_by("-created_at", "-id")[:5]
        ]
        recent_reviews = [
            self._serialize_review(item)
            for item in Review.objects.filter(user=user).select_related("hotel", "order").order_by("-created_at", "-id")[:5]
        ]
        agent_hints = self._build_customer_service_agent_hints(
            requested_order=requested_order,
            recent_orders=recent_order_models,
            recent_notices=recent_notices,
        )

        return {
            "now": timezone.localtime().isoformat(timespec="seconds"),
            "supported_topics": list(SUPPORTED_CUSTOMER_SERVICE_TOPICS),
            "dictionaries_json": self.prompt_service.dumps(self._build_dictionary_payload()),
            "user_profile_json": self.prompt_service.dumps(
                {
                    "id": getattr(user, "id", None),
                    "username": getattr(user, "username", ""),
                    "email": getattr(user, "email", ""),
                    "is_authenticated": getattr(user, "is_authenticated", False),
                }
            ),
            "requested_order_json": self.prompt_service.dumps(
                self._serialize_order(requested_order) if requested_order else None
            ),
            "requested_hotel_json": self.prompt_service.dumps(
                self._serialize_hotel(requested_hotel) if requested_hotel else None
            ),
            "requested_hotel_room_types_json": self.prompt_service.dumps(room_types),
            "recent_orders_json": self.prompt_service.dumps(recent_orders),
            "recommended_hotels_json": self.prompt_service.dumps(recommended_hotels),
            "recent_notices_json": self.prompt_service.dumps(recent_notices),
            "recent_reviews_json": self.prompt_service.dumps(recent_reviews),
            "agent_hints_json": self.prompt_service.dumps(agent_hints),
            "conversation_summary": (conversation_summary or "").strip(),
        }

    def _build_customer_service_agent_hints(
        self,
        *,
        requested_order: BookingOrder | None,
        recent_orders: list[BookingOrder],
        recent_notices: list[dict[str, Any]],
    ) -> dict[str, Any]:
        cancellable_statuses = {
            BookingOrder.STATUS_PENDING_PAYMENT,
            BookingOrder.STATUS_PAID,
            BookingOrder.STATUS_CONFIRMED,
            BookingOrder.STATUS_REFUNDING,
        }
        cancellable_orders = [
            {
                "id": order.id,
                "order_no": order.order_no,
                "status": order.status,
                "status_label": order.get_status_display(),
                "payment_status": order.payment_status,
                "payment_status_label": order.get_payment_status_display(),
            }
            for order in recent_orders
            if order.status in cancellable_statuses
        ]
        unpaid_orders = [
            {
                "id": order.id,
                "order_no": order.order_no,
                "status": order.status,
                "status_label": order.get_status_display(),
                "payment_status": order.payment_status,
                "payment_status_label": order.get_payment_status_display(),
            }
            for order in recent_orders
            if order.payment_status == BookingOrder.PAYMENT_UNPAID
        ]

        suggested_actions = [
            {
                "id": "query_order_status",
                "description": "查询订单状态与支付状态",
                "write": False,
                "endpoint": "GET /api/v1/user/orders/{id}",
                "requires_confirmation": False,
            },
            {
                "id": "cancel_order",
                "description": "取消订单（写操作）",
                "write": True,
                "endpoint": "POST /api/v1/user/orders/cancel",
                "requires_confirmation": True,
            },
            {
                "id": "pay_order",
                "description": "继续支付订单（写操作）",
                "write": True,
                "endpoint": "POST /api/v1/user/orders/pay",
                "requires_confirmation": True,
            },
            {
                "id": "apply_invoice",
                "description": "提交发票申请（写操作）",
                "write": True,
                "endpoint": "POST /api/v1/user/invoices/apply",
                "requires_confirmation": True,
            },
            {
                "id": "query_notices",
                "description": "查询最近通知",
                "write": False,
                "endpoint": "GET /api/v1/user/notices",
                "requires_confirmation": False,
            },
        ]

        return {
            "safety_policy": {
                "allow_write_operations": False,
                "write_requires_user_confirmation": True,
                "must_use_user_owned_data_only": True,
            },
            "requested_order_id": requested_order.id if requested_order else None,
            "cancellable_orders": cancellable_orders[:5],
            "unpaid_orders": unpaid_orders[:5],
            "recent_notice_count": len(recent_notices),
            "suggested_actions": suggested_actions,
        }

    def _build_customer_service_action_response(
        self,
        *,
        user: Any,
        order_id: int | None,
        question: str,
    ) -> dict[str, Any]:
        requested_order = BookingOrder.objects.filter(user=user).select_related("hotel", "room_type").filter(id=order_id).first() if order_id else None
        recent_orders = list(
            BookingOrder.objects.filter(user=user).select_related("hotel", "room_type").order_by("-id")[:5]
        )
        intent = self._detect_customer_service_intent(question)
        cancellable_statuses = {
            BookingOrder.STATUS_PENDING_PAYMENT,
            BookingOrder.STATUS_PAID,
            BookingOrder.STATUS_CONFIRMED,
            BookingOrder.STATUS_REFUNDING,
        }
        unpaid_statuses = {
            BookingOrder.STATUS_PENDING_PAYMENT,
            BookingOrder.STATUS_PAID,
        }

        preferred_order = requested_order or (recent_orders[0] if recent_orders else None)
        unpaid_order = next(
            (
                order
                for order in recent_orders
                if order.payment_status == BookingOrder.PAYMENT_UNPAID or order.status in unpaid_statuses
            ),
            None,
        )
        cancellable_order = next((order for order in recent_orders if order.status in cancellable_statuses), None)

        def build_action_query(
            *,
            target_order: BookingOrder | None = None,
            action: str | None = None,
            carry_question: bool = False,
        ) -> dict[str, str]:
            query: dict[str, str] = {
                "source": "ai",
                "intent": intent,
            }
            if target_order is not None:
                query["order_id"] = str(target_order.id)
            if action:
                query["action"] = action
            if carry_question:
                normalized_question = (question or "").strip()
                if normalized_question:
                    query["ask"] = normalized_question[:120]
                query["from"] = "ai-chat"
            return query

        def build_option(
            *,
            option_type: str,
            label: str,
            value: str,
            route: str,
            description: str = "",
            query: dict[str, str] | None = None,
            requires_confirmation: bool = False,
        ) -> dict[str, Any]:
            normalized_query = {str(k): str(v) for k, v in (query or {}).items() if v is not None}
            tracking_seed = f"{option_type}:{route}:{value}:{intent}"
            tracking_id = re.sub(r"[^a-z0-9_-]+", "-", tracking_seed.lower()).strip("-")[:64]
            return {
                "type": option_type,
                "label": label,
                "value": value,
                "description": description,
                "route": route,
                "query": normalized_query,
                "action_type": "navigate",
                "target": route,
                "params": normalized_query,
                "requires_confirmation": requires_confirmation,
                "priority": self._calc_customer_service_action_priority(intent=intent, option_type=option_type),
                "tracking_id": tracking_id or option_type,
                "source_scene": "customer_service",
            }
        options: list[dict[str, Any]] = []

        if intent == "booking_request":
            options.append(
                build_option(
                    option_type="navigate_ai_booking",
                    label="切换到 AI 订房助手",
                    value="ai-booking",
                    route="/ai-booking",
                    description="订酒店和比价更适合在订房助手中完成",
                    query=build_action_query(carry_question=True),
                )
            )

        if intent == "review":
            options.append(
                build_option(
                    option_type="navigate_reviews",
                    label="查看我的评价",
                    value="my-reviews",
                    route="/my/reviews",
                    description="查看你的评价记录与商家回复",
                    query=build_action_query(),
                )
            )

        if preferred_order is not None:
            options.append(
                build_option(
                    option_type="navigate_order_detail",
                    label="查看订单详情",
                    value=preferred_order.order_no,
                    route=f"/my/orders/{preferred_order.id}",
                    description=f"{preferred_order.order_no} · {preferred_order.get_status_display()}",
                    query=build_action_query(target_order=preferred_order),
                )
            )

        if unpaid_order is not None:
            options.append(
                build_option(
                    option_type="navigate_payment",
                    label="去支付",
                    value=unpaid_order.order_no,
                    route=f"/payment/{unpaid_order.id}",
                    description="继续完成订单支付",
                    query=build_action_query(target_order=unpaid_order),
                )
            )

        if cancellable_order is not None:
            options.append(
                build_option(
                    option_type="navigate_cancel_order",
                    label="取消订单",
                    value=cancellable_order.order_no,
                    route=f"/my/orders/{cancellable_order.id}",
                    description="前往订单详情并打开取消流程",
                    query=build_action_query(target_order=cancellable_order, action="cancel"),
                    requires_confirmation=True,
                )
            )

        if requested_order is not None and requested_order.status in cancellable_statuses:
            should_append_requested_cancel = cancellable_order is None or requested_order.id != cancellable_order.id
            if should_append_requested_cancel:
                options.append(
                    build_option(
                        option_type="navigate_cancel_order",
                        label="取消当前订单",
                        value=requested_order.order_no,
                        route=f"/my/orders/{requested_order.id}",
                        description="当前对话关联订单可取消",
                        query=build_action_query(target_order=requested_order, action="cancel"),
                        requires_confirmation=True,
                    )
                )

        options.extend(
            [
                build_option(
                    option_type="navigate_order_list",
                    label="查看我的订单",
                    value="order-list",
                    route="/my/orders",
                    description="进入订单中心查看全部订单",
                    query=build_action_query(),
                ),
                build_option(
                    option_type="navigate_invoice",
                    label="发票中心",
                    value="invoice-center",
                    route="/my/invoices",
                    description="查看发票申请与开票记录",
                    query=build_action_query(),
                ),
                build_option(
                    option_type="navigate_notification",
                    label="通知中心",
                    value="notification-center",
                    route="/my/notifications",
                    description="查看系统通知与提醒",
                    query=build_action_query(),
                ),
                build_option(
                    option_type="navigate_help",
                    label="帮助中心",
                    value="help-center",
                    route="/help",
                    description="查看更多常见问题与人工支持入口",
                    query=build_action_query(),
                ),
            ]
        )

        deduplicated_options: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for option in options:
            key = (
                str(option.get("type", "")),
                str(option.get("route", "")),
                json.dumps(option.get("query", {}), ensure_ascii=False, sort_keys=True),
            )
            if key in seen:
                continue
            seen.add(key)
            deduplicated_options.append(option)

        deduplicated_options.sort(key=lambda item: (int(item.get("priority", 99)), str(item.get("label", ""))))

        return {
            "intent": "customer_service_actions",
            "phase": "quick_actions",
            "context": {
                "detected_intent": intent,
                "requested_order_id": requested_order.id if requested_order else None,
                "preferred_order_id": preferred_order.id if preferred_order else None,
                "unpaid_order_id": unpaid_order.id if unpaid_order else None,
                "cancellable_order_id": cancellable_order.id if cancellable_order else None,
            },
            "options": deduplicated_options[:6],
        }

    def _detect_customer_service_intent(self, question: str) -> str:
        content = (question or "").strip().lower()
        if not content:
            return "general"

        if any(keyword in content for keyword in ("取消", "退订", "撤销", "不住", "取消订单")):
            return "cancel_order"
        if any(keyword in content for keyword in ("支付", "付款", "补款", "付钱", "未支付")):
            return "pay_order"
        if any(keyword in content for keyword in ("发票", "开票", "报销")):
            return "invoice"
        if any(keyword in content for keyword in ("通知", "消息", "提醒")):
            return "notification"
        if any(keyword in content for keyword in ("评价", "点评", "评论", "打分", "评分")):
            return "review"
        if any(keyword in content for keyword in ("订酒店", "预订", "找酒店", "比价", "推荐酒店", "房型")):
            return "booking_request"
        if any(keyword in content for keyword in ("订单", "状态", "进度", "详情")):
            return "order_status"
        return "general"

    def _calc_customer_service_action_priority(self, *, intent: str, option_type: str) -> int:
        base_priority = {
            "navigate_cancel_order": 25,
            "navigate_payment": 30,
            "navigate_order_detail": 35,
            "navigate_reviews": 40,
            "navigate_order_list": 45,
            "navigate_invoice": 50,
            "navigate_notification": 55,
            "navigate_help": 65,
            "navigate_ai_booking": 20,
        }
        priority = base_priority.get(option_type, 70)
        intent_boost_map = {
            "cancel_order": {"navigate_cancel_order": -20, "navigate_order_detail": -10},
            "pay_order": {"navigate_payment": -20, "navigate_order_detail": -10},
            "invoice": {"navigate_invoice": -20},
            "notification": {"navigate_notification": -20},
            "review": {"navigate_reviews": -20},
            "booking_request": {"navigate_ai_booking": -25},
            "order_status": {"navigate_order_detail": -15, "navigate_order_list": -10},
        }
        priority += intent_boost_map.get(intent, {}).get(option_type, 0)
        return max(priority, 1)

    def _build_booking_assistant_prompt_context(
        self,
        *,
        user: Any,
        question: str,
        hotel_id: int | None,
        booking_context: dict[str, Any] | None,
        conversation_summary: str,
    ) -> dict[str, Any]:
        context = self._normalize_booking_context(booking_context)
        cities = self._list_available_cities()

        selected_hotel = None
        selected_hotel_id = context.get("selected_hotel_id")
        if hotel_id:
            selected_hotel = Hotel.objects.filter(id=hotel_id, status=Hotel.STATUS_ONLINE).first()
        elif selected_hotel_id:
            selected_hotel = Hotel.objects.filter(id=selected_hotel_id, status=Hotel.STATUS_ONLINE).first()

        return {
            "now": timezone.localtime().isoformat(timespec="seconds"),
            "user_profile_json": self.prompt_service.dumps(
                {
                    "id": getattr(user, "id", None),
                    "username": getattr(user, "username", ""),
                }
            ),
            "question": question,
            "booking_context_json": self.prompt_service.dumps(context),
            "available_cities_json": self.prompt_service.dumps(cities),
            "selected_hotel_json": self.prompt_service.dumps(self._serialize_hotel(selected_hotel) if selected_hotel else None),
            "conversation_summary": (conversation_summary or "").strip(),
        }

    def _build_dictionary_payload(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "hotel_status": self._choice_payload(Hotel.STATUS_CHOICES),
            "room_status": self._choice_payload(RoomType.STATUS_CHOICES),
            "room_bed_type": self._choice_payload(RoomType.BED_TYPE_CHOICES),
            "order_status": self._choice_payload(BookingOrder.STATUS_CHOICES),
            "payment_status": self._choice_payload(BookingOrder.PAYMENT_STATUS_CHOICES),
        }

    def _choice_payload(self, choices: list[tuple[str, str]]) -> list[dict[str, str]]:
        return [{"value": value, "label": label} for value, label in choices]

    def _serialize_order(self, order: BookingOrder) -> dict[str, Any]:
        return {
            "id": order.id,
            "order_no": order.order_no,
            "hotel_id": order.hotel_id,
            "hotel_name": order.hotel.name,
            "room_type_id": order.room_type_id,
            "room_type_name": order.room_type.name,
            "status": order.status,
            "status_label": order.get_status_display(),
            "payment_status": order.payment_status,
            "payment_status_label": order.get_payment_status_display(),
            "check_in_date": order.check_in_date.isoformat(),
            "check_out_date": order.check_out_date.isoformat(),
            "guest_name": order.guest_name,
            "guest_count": order.guest_count,
            "room_no": order.room_no,
            "pay_amount": str(order.pay_amount),
            "created_at": timezone.localtime(order.created_at).isoformat(timespec="seconds"),
        }

    def _serialize_hotel(self, hotel: Hotel) -> dict[str, Any]:
        return {
            "id": hotel.id,
            "name": hotel.name,
            "city": hotel.city,
            "address": hotel.address,
            "star": hotel.star,
            "phone": hotel.phone,
            "description": hotel.description,
            "min_price": str(hotel.min_price),
            "rating": str(hotel.rating),
            "status": hotel.status,
            "status_label": hotel.get_status_display(),
            "is_recommended": hotel.is_recommended,
            "latitude": float(hotel.latitude) if hotel.latitude is not None else None,
            "longitude": float(hotel.longitude) if hotel.longitude is not None else None,
        }

    def _serialize_room_type(self, room_type: RoomType) -> dict[str, Any]:
        return {
            "id": room_type.id,
            "name": room_type.name,
            "bed_type": room_type.bed_type,
            "bed_type_label": room_type.get_bed_type_display(),
            "area": room_type.area,
            "breakfast_count": room_type.breakfast_count,
            "base_price": str(room_type.base_price),
            "max_guest_count": room_type.max_guest_count,
            "stock": room_type.stock,
            "status": room_type.status,
            "status_label": room_type.get_status_display(),
        }

    def _serialize_notice(self, notice: SystemNotice) -> dict[str, Any]:
        return {
            "id": notice.id,
            "type": notice.notice_type,
            "type_label": notice.get_notice_type_display(),
            "title": notice.title,
            "content": notice.content,
            "is_read": notice.is_read,
            "created_at": timezone.localtime(notice.created_at).isoformat(timespec="seconds"),
        }

    def _serialize_review(self, review: Review) -> dict[str, Any]:
        return {
            "id": review.id,
            "order_id": review.order_id,
            "hotel_id": review.hotel_id,
            "hotel_name": review.hotel.name if review.hotel_id else "",
            "score": review.score,
            "content": review.content,
            "reply_content": review.reply_content,
            "created_at": timezone.localtime(review.created_at).isoformat(timespec="seconds"),
        }

    def _build_booking_assistant_response(
        self,
        *,
        user: Any,
        question: str,
        requested_scene: str,
        hotel_id: int | None,
        booking_context: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        context = self._normalize_booking_context(booking_context)
        cities = self._list_available_cities()
        llm_slots = self._extract_booking_slots_with_llm(question=question, cities=cities)
        enriched_preferences = self._build_booking_preferences(question=question, llm_slots=llm_slots, context=context)
        context.update(enriched_preferences)

        if self._should_reset_booking_context(question):
            context = self._fresh_booking_context()
        elif llm_slots.get("reset"):
            context = self._fresh_booking_context()
        elif self._should_clear_selected_hotel(question):
            context["selected_hotel_id"] = None
        elif llm_slots.get("switch_hotel"):
            context["selected_hotel_id"] = None

        if not self._should_enter_booking_flow(
            question,
            hotel_id=hotel_id,
            booking_context=context,
            force_booking_flow=requested_scene == "booking_assistant",
        ):
            return None

        customer_service_intent = self._detect_booking_to_customer_service_intent(question)
        if customer_service_intent:
            normalized_question = (question or "").strip()
            switch_query: dict[str, str] = {
                "source": "ai",
                "intent": customer_service_intent,
                "from": "ai-booking",
            }
            if normalized_question:
                switch_query["ask"] = normalized_question[:120]
            return {
                "intent": "hotel_booking",
                "phase": "switch_to_customer_service",
                "context": context,
                "options": [
                    {
                        "type": "navigate_ai_customer_service",
                        "label": "切换到 AI 智能客服",
                        "value": "ai-chat",
                        "description": "订单、退款、发票、会员等问题由客服助手处理更准确",
                        "route": "/ai-chat",
                        "query": switch_query,
                        "action_type": "navigate",
                        "target": "/ai-chat",
                        "params": switch_query,
                        "requires_confirmation": False,
                        "priority": 10,
                        "tracking_id": "navigate-ai-customer-service",
                        "source_scene": "booking_assistant",
                    }
                ],
                "answer": "这个问题更适合由 AI 智能客服处理。我已为您准备了一键切换入口，点击即可继续。",
            }

        selected_city_from_question = self._extract_city_from_question(question, cities)
        if not selected_city_from_question and llm_slots.get("selected_city"):
            selected_city_from_question = self._extract_city_from_question(str(llm_slots["selected_city"]), cities)
        selected_city = context.get("selected_city")
        if selected_city_from_question:
            selected_city = selected_city_from_question
            context["selected_city"] = selected_city_from_question
            if context.get("selected_hotel_id"):
                context["selected_hotel_id"] = None
        matched_hotel = self._resolve_hotel_from_booking_context(
            question=question,
            hotel_id=hotel_id,
            selected_city=selected_city,
            booking_context=context,
            hotel_keyword=str(llm_slots.get("hotel_keyword") or ""),
        )

        if isinstance(matched_hotel, list):
            options = [self._build_hotel_option(item) for item in matched_hotel[:6]]
            answer = "我识别到您提到了多个可预订酒店，先点一个酒店，我直接带您看该酒店可下单的房型。"
            context["selected_hotel_id"] = None
            context["last_hotel_ids"] = [item.id for item in matched_hotel[:6]]
            return {
                "intent": "hotel_booking",
                "phase": "select_hotel",
                "context": context,
                "options": options,
                "answer": answer,
            }

        if matched_hotel is not None:
            room_types = list(
                RoomType.objects.filter(hotel=matched_hotel, status=RoomType.STATUS_ONLINE).order_by("base_price", "id")[:8]
            )
            answer = self._build_room_type_answer(matched_hotel, room_types)
            context["selected_city"] = matched_hotel.city
            context["selected_hotel_id"] = matched_hotel.id
            return {
                "intent": "hotel_booking",
                "phase": "select_room_type",
                "context": context,
                "options": [self._build_room_type_option(matched_hotel, room_type) for room_type in room_types],
                "answer": answer,
            }

        if selected_city:
            nearby_request = self._extract_nearby_request(question=question, llm_slots=llm_slots, selected_city=selected_city, context=context)
            if nearby_request is not None:
                poi_name = nearby_request["poi_name"]
                poi_lat = nearby_request["poi_lat"]
                poi_lng = nearby_request["poi_lng"]
                radius_km = nearby_request["radius_km"]
                context["nearby_poi_name"] = poi_name
                context["nearby_poi_lat"] = poi_lat
                context["nearby_poi_lng"] = poi_lng
                context["nearby_radius_km"] = radius_km
                hotels_with_distance = self._find_nearby_hotels(selected_city=selected_city, poi_lat=poi_lat, poi_lng=poi_lng, radius_km=radius_km)
                if hotels_with_distance:
                    options = [
                        self._build_hotel_option(
                            item["hotel"],
                            distance_km=item["distance_km"],
                            poi_name=poi_name,
                            navigate_to_detail=True,
                        )
                        for item in hotels_with_distance[:8]
                    ]
                    answer = (
                        f"已为您找到离{poi_name}最近的酒店（{selected_city}，{radius_km}公里内）。"
                        "您可以直接点酒店查看地图与距离，也可以回复“继续订这个”我直接带您选房型。"
                    )
                    context["last_hotel_ids"] = [item["hotel"].id for item in hotels_with_distance[:8]]
                    return {
                        "intent": "hotel_booking",
                        "phase": "select_hotel",
                        "context": context,
                        "options": options,
                        "answer": answer,
                    }
                answer = (
                    f"我暂时没找到{selected_city}里距离{poi_name} {radius_km}公里内的酒店。"
                    "您可以告诉我更大的范围（例如 8 公里内），我马上重新筛选。"
                )
                return {
                    "intent": "hotel_booking",
                    "phase": "clarify_radius",
                    "context": context,
                    "options": [
                        {"type": "select_radius", "label": "5 公里内", "value": "5"},
                        {"type": "select_radius", "label": "8 公里内", "value": "8"},
                        {"type": "select_radius", "label": "10 公里内", "value": "10"},
                    ],
                    "answer": answer,
                }

            if any(keyword in question for keyword in self.BOOKING_NEARBY_KEYWORDS):
                answer = (
                    f"我理解您想找离某个地点最近的酒店。为了给您精确结果，请告诉我{selected_city}的具体地点（如商圈/地标）"
                    "，以及大概范围（例如 3 公里内或 5 公里内）。"
                )
                return {
                    "intent": "hotel_booking",
                    "phase": "clarify_poi",
                    "context": context,
                    "options": [
                        {"type": "clarify_poi", "label": f"{selected_city}市中心 3 公里内", "value": "center_3"},
                        {"type": "clarify_poi", "label": f"{selected_city}地铁站 5 公里内", "value": "metro_5"},
                    ],
                    "answer": answer,
                }

            hotels = self._list_hotels_for_city(selected_city)
            hotels = self._rank_hotels_by_preferences(hotels, context)
            if hotels:
                top_hotels = hotels[:8]
                repeated = self._is_repeated_hotel_options(top_hotels, context)
                answer = self._build_hotel_list_answer(selected_city=selected_city, hotels=top_hotels, context=context, repeated=repeated)
                context["last_hotel_ids"] = [hotel.id for hotel in top_hotels]
                return {
                    "intent": "hotel_booking",
                    "phase": "select_hotel",
                    "context": context,
                    "options": [self._build_hotel_option(hotel) for hotel in top_hotels],
                    "answer": answer,
                }

            answer = f"{selected_city} 暂时没有可预订酒店，您可以换一个城市，我把当前系统里可选城市都列给您。"
            context["selected_city"] = None
            context["selected_hotel_id"] = None
            return {
                "intent": "hotel_booking",
                "phase": "select_city",
                "context": context,
                "options": [self._build_city_option(city) for city in cities[:12]],
                "answer": answer,
            }

        answer = "可以，我来帮您直接订酒店。先选城市，我只展示系统里当前可预订的城市，您点一下我就继续带您选酒店。"
        return {
            "intent": "hotel_booking",
            "phase": "select_city",
            "context": context,
            "options": [self._build_city_option(city) for city in cities[:12]],
            "answer": answer,
        }

    def _build_booking_preferences(
        self,
        *,
        question: str,
        llm_slots: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        sort_by = str(llm_slots.get("sort_by") or context.get("sort_by") or "").strip() or None
        budget_max = self._extract_budget_max(question)
        if budget_max is None and llm_slots.get("budget_max"):
            try:
                budget_max = int(llm_slots["budget_max"])
            except (TypeError, ValueError):
                budget_max = None
        if budget_max is None:
            budget_max = context.get("budget_max")

        min_rating = self._extract_min_rating(question)
        if min_rating is None and llm_slots.get("min_rating") is not None:
            try:
                min_rating = float(llm_slots["min_rating"])
            except (TypeError, ValueError):
                min_rating = None
        if min_rating is None:
            min_rating = context.get("min_rating")

        needs_family = bool(context.get("needs_family", False))
        needs_business = bool(context.get("needs_business", False))
        prefer_transport = bool(context.get("prefer_transport", False))

        if any(keyword in question for keyword in self.BOOKING_FAMILY_KEYWORDS):
            needs_family = True
        if any(keyword in question for keyword in self.BOOKING_BUSINESS_KEYWORDS):
            needs_business = True
        if any(keyword in question for keyword in self.BOOKING_CENTER_KEYWORDS):
            prefer_transport = True

        if sort_by is None:
            if any(keyword in question for keyword in self.BOOKING_CHEAP_KEYWORDS):
                sort_by = "price_asc"
            elif "最贵" in question or "高端" in question:
                sort_by = "price_desc"
            elif any(keyword in question for keyword in self.BOOKING_HIGH_RATING_KEYWORDS):
                sort_by = "rating_desc"

        return {
            "intent": "hotel_booking",
            "selected_city": context.get("selected_city"),
            "selected_hotel_id": context.get("selected_hotel_id"),
            "sort_by": sort_by,
            "budget_max": budget_max,
            "min_rating": min_rating,
            "needs_family": needs_family,
            "needs_business": needs_business,
            "prefer_transport": prefer_transport,
            "last_hotel_ids": context.get("last_hotel_ids") or [],
            "nearby_poi_name": context.get("nearby_poi_name") or None,
            "nearby_poi_lat": context.get("nearby_poi_lat"),
            "nearby_poi_lng": context.get("nearby_poi_lng"),
            "nearby_radius_km": context.get("nearby_radius_km") if isinstance(context.get("nearby_radius_km"), (int, float)) else None,
        }

    def _detect_booking_to_customer_service_intent(self, question: str) -> str | None:
        content = (question or "").strip().lower()
        if not content:
            return None

        if any(keyword in content for keyword in ("客服", "人工", "转人工")):
            return "customer_service"

        intent_map = [
            (("取消", "退订", "撤销", "退款"), "cancel_or_refund"),
            (("支付", "付款", "补款", "扣款", "支付失败"), "payment"),
            (("发票", "开票", "报销"), "invoice"),
            (("会员", "积分", "等级", "权益", "成长值"), "membership"),
            (("通知", "消息", "提醒"), "notification"),
        ]
        for keywords, intent in intent_map:
            if any(keyword in content for keyword in keywords):
                return intent

        has_order_keyword = any(keyword in content for keyword in ("订单", "订单号", "改期", "改签", "售后", "投诉"))
        has_service_action = any(keyword in content for keyword in ("状态", "进度", "查询", "处理", "问题", "失败"))
        if has_order_keyword and has_service_action:
            return "order_service"

        return None

    def _fresh_booking_context(self) -> dict[str, Any]:
        return {
            "intent": "hotel_booking",
            "selected_city": None,
            "selected_hotel_id": None,
            "sort_by": None,
            "budget_max": None,
            "min_rating": None,
            "needs_family": False,
            "needs_business": False,
            "prefer_transport": False,
            "last_hotel_ids": [],
            "nearby_poi_name": None,
            "nearby_poi_lat": None,
            "nearby_poi_lng": None,
            "nearby_radius_km": None,
        }

    def _extract_nearby_request(
        self,
        *,
        question: str,
        llm_slots: dict[str, Any],
        selected_city: str | None,
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not selected_city:
            return None

        radius_km = self._extract_radius_km(question)
        if radius_km is None and llm_slots.get("nearby_radius_km") is not None:
            try:
                parsed = int(llm_slots.get("nearby_radius_km"))
                if 1 <= parsed <= 30:
                    radius_km = parsed
            except (TypeError, ValueError):
                radius_km = None
        if radius_km is None:
            radius_km = 3

        has_nearby_keyword = any(keyword in question for keyword in self.BOOKING_NEARBY_KEYWORDS)
        existing_poi_name = context.get("nearby_poi_name")
        existing_poi_lat = context.get("nearby_poi_lat")
        existing_poi_lng = context.get("nearby_poi_lng")
        if not has_nearby_keyword and not (existing_poi_name and radius_km is not None):
            return None

        poi = self._match_poi(question, selected_city)
        if poi is None and existing_poi_name and isinstance(existing_poi_lat, (int, float)) and isinstance(existing_poi_lng, (int, float)):
            return {
                "poi_name": str(existing_poi_name),
                "poi_lat": float(existing_poi_lat),
                "poi_lng": float(existing_poi_lng),
                "radius_km": radius_km,
            }
        if poi is None:
            return None
        return {
            "poi_name": poi["name"],
            "poi_lat": float(poi["lat"]),
            "poi_lng": float(poi["lng"]),
            "radius_km": radius_km,
        }

    def _extract_radius_km(self, question: str) -> int | None:
        match = re.search(r"(\d{1,2})\s*(公里|km|KM)", question)
        if not match:
            return None
        try:
            value = int(match.group(1))
        except (TypeError, ValueError):
            return None
        if value < 1 or value > 30:
            return None
        return value

    def _match_poi(self, question: str, selected_city: str) -> dict[str, Any] | None:
        for poi in self.POI_CANDIDATES:
            if poi["city"] != selected_city:
                continue
            for alias in poi["aliases"]:
                if alias in question:
                    return poi
        poi_keyword = self._extract_poi_keyword(question)
        if poi_keyword:
            geocoded = self._geocode_poi_free(city=selected_city, poi_keyword=poi_keyword)
            if geocoded is not None:
                return geocoded
        return None

    def _extract_poi_keyword(self, question: str) -> str | None:
        normalized = question.strip()
        patterns = [
            r"离(.+?)(?:最近|附近)",
            r"(.+?)附近",
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if not match:
                continue
            value = (match.group(1) or "").strip(" ，。,.？！?、")
            if len(value) >= 2:
                return value
        return None

    def _geocode_poi_free(self, *, city: str, poi_keyword: str) -> dict[str, Any] | None:
        query = f"{city}{poi_keyword}"
        params = urlencode({"q": query, "format": "json", "limit": 1, "addressdetails": 0})
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        req = Request(url, headers={"User-Agent": "HoteLink/1.0 (booking-assistant)"})
        try:
            with urlopen(req, timeout=2.5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None
        if not isinstance(payload, list) or not payload:
            return None
        first = payload[0]
        try:
            lat = float(first.get("lat"))
            lng = float(first.get("lon"))
        except (TypeError, ValueError):
            return None
        return {
            "name": poi_keyword,
            "city": city,
            "lat": lat,
            "lng": lng,
            "aliases": [poi_keyword],
        }

    def _find_nearby_hotels(
        self,
        *,
        selected_city: str,
        poi_lat: float,
        poi_lng: float,
        radius_km: int,
    ) -> list[dict[str, Any]]:
        hotels = Hotel.objects.filter(
            city=selected_city,
            status=Hotel.STATUS_ONLINE,
            latitude__isnull=False,
            longitude__isnull=False,
        ).order_by("-is_recommended", "-rating", "min_price", "id")[:50]

        ranked: list[dict[str, Any]] = []
        for hotel in hotels:
            distance_km = self._haversine_km(
                poi_lat,
                poi_lng,
                float(hotel.latitude),
                float(hotel.longitude),
            )
            if distance_km <= radius_km:
                ranked.append({"hotel": hotel, "distance_km": round(distance_km, 2)})

        return sorted(ranked, key=lambda item: (item["distance_km"], float(item["hotel"].min_price or 0), -float(item["hotel"].rating or 0)))

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius * c

    def _extract_budget_max(self, question: str) -> int | None:
        match = re.search(r"(?:预算|人均|大概|控制在)?\s*(\d{2,5})(?:元|块|以内|以下|左右)?", question)
        if not match:
            return None
        try:
            value = int(match.group(1))
        except (TypeError, ValueError):
            return None
        if value < 80 or value > 20000:
            return None
        return value

    def _extract_min_rating(self, question: str) -> float | None:
        match = re.search(r"([34](?:\.\d)?)\s*分(?:以上)?", question)
        if match:
            try:
                return float(match.group(1))
            except (TypeError, ValueError):
                return None
        if "高评分" in question or "评分高" in question:
            return 4.5
        return None

    def _list_hotels_for_city(self, city: str) -> list[Hotel]:
        return list(
            Hotel.objects.filter(city=city, status=Hotel.STATUS_ONLINE)
            .order_by("-is_recommended", "-rating", "min_price", "id")[:16]
        )

    def _rank_hotels_by_preferences(self, hotels: list[Hotel], context: dict[str, Any]) -> list[Hotel]:
        filtered = hotels
        budget_max = context.get("budget_max")
        min_rating = context.get("min_rating")
        sort_by = context.get("sort_by")

        if isinstance(budget_max, int):
            filtered_budget = [hotel for hotel in filtered if hotel.min_price and float(hotel.min_price) <= budget_max]
            if filtered_budget:
                filtered = filtered_budget

        if isinstance(min_rating, (float, int)):
            filtered_rating = [hotel for hotel in filtered if hotel.rating and float(hotel.rating) >= float(min_rating)]
            if filtered_rating:
                filtered = filtered_rating

        if sort_by == "price_asc":
            return sorted(filtered, key=lambda hotel: (float(hotel.min_price or 0), -float(hotel.rating or 0), hotel.id))
        if sort_by == "rating_desc":
            return sorted(filtered, key=lambda hotel: (-float(hotel.rating or 0), float(hotel.min_price or 0), hotel.id))
        if sort_by == "price_desc":
            return sorted(filtered, key=lambda hotel: (-float(hotel.min_price or 0), -float(hotel.rating or 0), hotel.id))
        return sorted(filtered, key=lambda hotel: (-int(bool(hotel.is_recommended)), -float(hotel.rating or 0), float(hotel.min_price or 0), hotel.id))

    def _is_repeated_hotel_options(self, hotels: list[Hotel], context: dict[str, Any]) -> bool:
        last_ids = context.get("last_hotel_ids") or []
        if not isinstance(last_ids, list) or not last_ids:
            return False
        current_ids = [hotel.id for hotel in hotels]
        return current_ids == [int(item) for item in last_ids if isinstance(item, (int, str)) and str(item).isdigit()]

    def _build_hotel_list_answer(
        self,
        *,
        selected_city: str,
        hotels: list[Hotel],
        context: dict[str, Any],
        repeated: bool,
    ) -> str:
        sort_by = context.get("sort_by")
        budget_max = context.get("budget_max")
        min_rating = context.get("min_rating")
        prefer_transport = bool(context.get("prefer_transport"))
        needs_family = bool(context.get("needs_family"))
        needs_business = bool(context.get("needs_business"))

        reasons: list[str] = []
        if isinstance(budget_max, int):
            reasons.append(f"预算不高于¥{budget_max}")
        if isinstance(min_rating, (float, int)):
            reasons.append(f"评分至少{float(min_rating):.1f}")
        if needs_family:
            reasons.append("家庭出行偏好")
        if needs_business:
            reasons.append("商务出行偏好")
        if prefer_transport:
            reasons.append("交通便利偏好")

        reason_text = f"（已按{'、'.join(reasons)}筛选）" if reasons else ""
        transport_hint = "当前系统未提供实时地铁/市中心距离字段，我先按评分与价格为您做近似优选。" if prefer_transport else ""

        if repeated:
            return (
                f"{selected_city} 目前仍是这几家更匹配您的条件 {reason_text}。"
                f"{transport_hint}"
                "如果您愿意，我可以立刻换一个排序方式（最便宜/评分最高/推荐优先）继续给您精排。"
            )

        if sort_by == "price_asc":
            return f"已为您按“价格从低到高”筛到 {selected_city} 的可订酒店 {reason_text}。{transport_hint}先看这几家，点一家我就展开可下单房型。"
        if sort_by == "rating_desc":
            return f"已为您按“评分从高到低”筛到 {selected_city} 的可订酒店 {reason_text}。{transport_hint}先看这几家，点一家我就展开可下单房型。"
        if sort_by == "price_desc":
            return f"已为您按“价格从高到低”展示 {selected_city} 的可订酒店 {reason_text}。{transport_hint}先看这几家，点一家我就展开可下单房型。"
        return f"已为您切到{selected_city}，这里有 {len(hotels)} 家当前可预订酒店 {reason_text}。{transport_hint}点一家，我继续把房型直接展开给您。"

    def _should_enter_booking_flow(
        self,
        question: str,
        *,
        hotel_id: int | None,
        booking_context: dict[str, Any],
        force_booking_flow: bool = False,
    ) -> bool:
        if force_booking_flow:
            return True
        if hotel_id or booking_context.get("selected_hotel_id") or booking_context.get("selected_city"):
            return True
        if booking_context.get("intent") == "hotel_booking":
            return True
        if any(keyword in question for keyword in self.BOOKING_INTENT_KEYWORDS):
            return True
        return self._question_mentions_known_hotel(question)

    def _should_reset_booking_context(self, question: str) -> bool:
        return any(keyword in question for keyword in self.BOOKING_RESET_KEYWORDS)

    def _should_clear_selected_hotel(self, question: str) -> bool:
        return any(keyword in question for keyword in self.BOOKING_SWITCH_HOTEL_KEYWORDS)

    def _normalize_booking_context(self, booking_context: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(booking_context, dict):
            return {}
        selected_hotel_id = booking_context.get("selected_hotel_id")
        try:
            selected_hotel_id = int(selected_hotel_id) if selected_hotel_id else None
        except (TypeError, ValueError):
            selected_hotel_id = None
        selected_city = booking_context.get("selected_city") or None
        last_hotel_ids = booking_context.get("last_hotel_ids")
        if not isinstance(last_hotel_ids, list):
            last_hotel_ids = []
        return {
            "intent": booking_context.get("intent") or None,
            "selected_city": selected_city,
            "selected_hotel_id": selected_hotel_id,
            "sort_by": booking_context.get("sort_by") or None,
            "budget_max": booking_context.get("budget_max") if isinstance(booking_context.get("budget_max"), int) else None,
            "min_rating": booking_context.get("min_rating") if isinstance(booking_context.get("min_rating"), (int, float)) else None,
            "needs_family": bool(booking_context.get("needs_family", False)),
            "needs_business": bool(booking_context.get("needs_business", False)),
            "prefer_transport": bool(booking_context.get("prefer_transport", False)),
            "last_hotel_ids": last_hotel_ids,
            "nearby_poi_name": booking_context.get("nearby_poi_name") or None,
            "nearby_poi_lat": booking_context.get("nearby_poi_lat"),
            "nearby_poi_lng": booking_context.get("nearby_poi_lng"),
            "nearby_radius_km": booking_context.get("nearby_radius_km") if isinstance(booking_context.get("nearby_radius_km"), (int, float)) else None,
        }

    def _list_available_cities(self) -> list[str]:
        return list(Hotel.objects.filter(status=Hotel.STATUS_ONLINE).exclude(city="").values_list("city", flat=True).distinct().order_by("city"))

    def _extract_city_from_question(self, question: str, cities: list[str]) -> str | None:
        for poi in self.POI_CANDIDATES:
            for alias in poi["aliases"]:
                if alias in question and poi["city"] in cities:
                    return poi["city"]
        for city in sorted(cities, key=len, reverse=True):
            if city and city in question:
                return city
        return None

    def _resolve_hotel_from_booking_context(
        self,
        *,
        question: str,
        hotel_id: int | None,
        selected_city: str | None,
        booking_context: dict[str, Any],
        hotel_keyword: str = "",
    ) -> Hotel | list[Hotel] | None:
        queryset = Hotel.objects.filter(status=Hotel.STATUS_ONLINE)
        if selected_city:
            queryset = queryset.filter(city=selected_city)
        candidates = list(queryset.order_by("-is_recommended", "-rating", "min_price", "id")[:20])
        matched = [
            hotel
            for hotel in candidates
            if self._hotel_matches_question(hotel=hotel, question=question, hotel_keyword=hotel_keyword)
        ]
        if len(matched) == 1:
            return matched[0]
        if len(matched) > 1:
            return matched

        target_hotel_id = hotel_id or booking_context.get("selected_hotel_id")
        if target_hotel_id:
            target_hotel = Hotel.objects.filter(id=target_hotel_id, status=Hotel.STATUS_ONLINE).first()
            if target_hotel and (not selected_city or target_hotel.city == selected_city):
                return target_hotel
        return None

    def _question_mentions_known_hotel(self, question: str) -> bool:
        if not question.strip():
            return False
        hotels = Hotel.objects.filter(status=Hotel.STATUS_ONLINE).values_list("name", flat=True)[:50]
        return any(name and name in question for name in hotels)

    def _hotel_matches_question(self, *, hotel: Hotel, question: str, hotel_keyword: str = "") -> bool:
        hotel_name = (hotel.name or "").strip()
        if not hotel_name:
            return False

        if hotel_name in question:
            return True

        normalized_question = self._normalize_match_text(question)
        normalized_hotel = self._normalize_match_text(hotel_name)
        normalized_keyword = self._normalize_match_text(hotel_keyword)
        if normalized_hotel and normalized_hotel in normalized_question:
            return True

        simplified_hotel = self._strip_hotel_suffix(normalized_hotel)
        if simplified_hotel and simplified_hotel in normalized_question:
            return True

        if normalized_keyword:
            if normalized_keyword in normalized_hotel:
                return True
            if normalized_keyword in self._strip_hotel_suffix(normalized_hotel):
                return True

        question_tokens = self._extract_match_tokens(question)
        hotel_tokens = self._extract_match_tokens(hotel_name)
        overlap = question_tokens.intersection(hotel_tokens)
        if len(overlap) >= 2:
            return True

        return False

    def _normalize_match_text(self, value: str) -> str:
        lowered = value.lower()
        lowered = re.sub(r"\s+", "", lowered)
        lowered = re.sub(r"[^\w\u4e00-\u9fff]", "", lowered)
        return lowered

    def _strip_hotel_suffix(self, value: str) -> str:
        return re.sub(r"(酒店|宾馆|旅馆|饭店|店)$", "", value)

    def _extract_match_tokens(self, value: str) -> set[str]:
        lowered = value.lower()
        tokens = set(re.findall(r"[a-z0-9]{3,}|[\u4e00-\u9fff]{2,}", lowered))
        stop_words = {"hotel", "hotellink", "酒店"}
        return {token for token in tokens if token not in stop_words}

    def _extract_booking_slots_with_llm(self, *, question: str, cities: list[str]) -> dict[str, Any]:
        if not self.is_available():
            return {}
        try:
            prompt_context = {
                "question": question,
                "available_cities_json": self.prompt_service.dumps(cities),
            }
            system_prompt = self.prompt_service.render("booking_assistant/slot_system.j2", **prompt_context)
            user_prompt = self.prompt_service.render("booking_assistant/slot_user.j2", **prompt_context)
            result = self.create_chat_completion(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            content = (result.get("content") or "").strip()
            if not content:
                return {}

            if "```" in content:
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)
            payload = json.loads(content)
            if not isinstance(payload, dict):
                return {}

            return {
                "selected_city": self._sanitize_slot_city(payload.get("selected_city"), cities),
                "hotel_keyword": self._sanitize_slot_hotel_keyword(payload.get("hotel_keyword")),
                "reset": bool(payload.get("reset", False)),
                "switch_hotel": bool(payload.get("switch_hotel", False)),
                "sort_by": self._sanitize_slot_sort_by(payload.get("sort_by")),
                "budget_max": self._sanitize_slot_int(payload.get("budget_max"), minimum=80, maximum=50000),
                "min_rating": self._sanitize_slot_float(payload.get("min_rating"), minimum=0, maximum=5),
                "nearby_radius_km": self._sanitize_slot_int(payload.get("nearby_radius_km"), minimum=1, maximum=30),
            }
        except Exception:
            return {}

    def _sanitize_slot_city(self, value: Any, cities: list[str]) -> str | None:
        if not value:
            return None
        text = str(value).strip()
        if not text:
            return None
        return text if text in cities else None

    def _sanitize_slot_hotel_keyword(self, value: Any) -> str | None:
        if not value:
            return None
        text = str(value).strip()
        if not text:
            return None
        if len(text) > 60:
            text = text[:60]
        return text

    def _sanitize_slot_sort_by(self, value: Any) -> str | None:
        allowed = {"price_asc", "rating_desc", "price_desc"}
        if not value:
            return None
        text = str(value).strip()
        return text if text in allowed else None

    def _sanitize_slot_int(self, value: Any, *, minimum: int, maximum: int) -> int | None:
        if value is None or value == "":
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        if parsed < minimum or parsed > maximum:
            return None
        return parsed

    def _sanitize_slot_float(self, value: Any, *, minimum: float, maximum: float) -> float | None:
        if value is None or value == "":
            return None
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        if parsed < minimum or parsed > maximum:
            return None
        return parsed

    def _build_city_option(self, city: str) -> dict[str, Any]:
        return {
            "type": "select_city",
            "label": city,
            "value": city,
            "payload": {
                "intent": "hotel_booking",
                "selected_city": city,
                "selected_hotel_id": None,
            },
        }

    def _build_hotel_option(
        self,
        hotel: Hotel,
        *,
        distance_km: float | None = None,
        poi_name: str | None = None,
        navigate_to_detail: bool = False,
    ) -> dict[str, Any]:
        description = f"{hotel.city} | {hotel.star}星 | 评分{hotel.rating} | ¥{hotel.min_price}起"
        query: dict[str, str] = {}
        if distance_km is not None:
            description = f"{description} | 距{poi_name or '目标点'}约{distance_km:.2f}km"
            query["distance_km"] = f"{distance_km:.2f}"
            if poi_name:
                query["poi"] = poi_name

        option = {
            "type": "select_hotel",
            "label": hotel.name,
            "value": str(hotel.id),
            "description": description,
            "payload": {
                "intent": "hotel_booking",
                "selected_city": hotel.city,
                "selected_hotel_id": hotel.id,
            },
        }
        if navigate_to_detail:
            option["type"] = "navigate_hotel"
            option["route"] = f"/hotels/{hotel.id}"
            option["query"] = query
        return option

    def _build_room_type_option(self, hotel: Hotel, room_type: RoomType) -> dict[str, Any]:
        breakfast_text = f"含{room_type.breakfast_count}早" if room_type.breakfast_count else "无早"
        return {
            "type": "navigate_booking",
            "label": room_type.name,
            "value": str(room_type.id),
            "description": (
                f"{room_type.get_bed_type_display()} | {room_type.area}㎡ | 可住{room_type.max_guest_count}人 | "
                f"{breakfast_text} | ¥{room_type.base_price}/晚"
            ),
            "route": "/booking",
            "query": {
                "hotel_id": str(hotel.id),
                "room_type_id": str(room_type.id),
                "room_name": room_type.name,
                "price": str(room_type.base_price),
                "hotel_name": hotel.name,
            },
        }

    def _build_room_type_answer(self, hotel: Hotel, room_types: list[RoomType]) -> str:
        if not room_types:
            return f"{hotel.name} 当前没有可直接预订的在线房型，您可以换一家酒店，我继续帮您筛。"
        return (
            f"已为您定位到 {hotel.name}。下面这些都是系统里当前可下单的房型，"
            "点任意一个房型，我直接带您进入订单填写页。"
        )


    # ──────────────────────────────────────────────────────────────────────
    # 以下为新增 AI 功能方法
    # ──────────────────────────────────────────────────────────────────────

    def _admin_chat(
        self,
        scene: str,
        system_context: dict,
        use_reasoning: bool = False,
        temperature: float = 0.3,
    ) -> str:
        """渲染管理端场景提示词并调用 LLM，返回原始文本。不可用时返回空串。"""
        if not self.is_available():
            return ""
        system_prompt = self.prompt_service.render_admin(scene, "system", **system_context)
        user_prompt = self.prompt_service.render_admin(scene, "user", **system_context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        model = None
        if use_reasoning and self._provider and self._provider.reasoning_model:
            model = self._provider.reasoning_model
        result = self.create_chat_completion(messages, model=model, temperature=temperature)
        return result.get("content", "")

    def _parse_json_response(self, text: str) -> dict | list | None:
        """从 LLM 响应中提取 JSON 对象或数组。"""
        import json
        text = text.strip()
        # 尝试去除 markdown 代码块
        text = re.sub(r"^```(?:json)?\n?", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n?```$", "", text, flags=re.MULTILINE)
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            # 尝试提取第一个 JSON 对象/数组
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    pass
        return None

    # ───────── 修复现有 "空壳" 视图：报表摘要 ─────────

    def generate_report_summary(
        self,
        *,
        hotel_id: int | None,
        start_date,
        end_date,
    ) -> dict:
        """生成酒店运营摘要报告（真实 LLM 调用）。"""
        from decimal import Decimal
        from django.db.models import Sum, Avg
        from apps.bookings.models import BookingOrder
        from apps.crm.models import Review

        qs = BookingOrder.objects.filter(
            check_in_date__gte=start_date,
            check_out_date__lte=end_date,
        )
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
            hotel = Hotel.objects.filter(id=hotel_id).first()
            hotel_scope = hotel.name if hotel else f"酒店 #{hotel_id}"
        else:
            hotel_scope = "全部酒店"

        total_orders = qs.count()
        paid_orders = qs.filter(payment_status=BookingOrder.PAYMENT_PAID).count()
        cancelled_orders = qs.filter(status=BookingOrder.STATUS_CANCELLED).count()
        cancellation_rate = round((cancelled_orders / total_orders * 100), 1) if total_orders else 0
        total_revenue = qs.filter(payment_status=BookingOrder.PAYMENT_PAID).aggregate(
            total=Sum("pay_amount")
        )["total"] or Decimal("0")
        avg_paid_price = (total_revenue / paid_orders).quantize(Decimal("0.01")) if paid_orders else Decimal("0")

        checked_in_count = BookingOrder.objects.filter(status=BookingOrder.STATUS_CHECKED_IN).count()
        total_stock = RoomType.objects.aggregate(total=Sum("stock"))["total"] or 0
        occupancy_rate = round((checked_in_count / total_stock * 100), 1) if total_stock else 0

        review_qs = Review.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        if hotel_id:
            review_qs = review_qs.filter(hotel_id=hotel_id)
        review_count = review_qs.count()
        avg_score = round(float(review_qs.aggregate(avg=Avg("score"))["avg"] or 0), 2)

        context = {
            "hotel_scope": hotel_scope,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "cancelled_orders": cancelled_orders,
            "cancellation_rate": cancellation_rate,
            "total_revenue": float(total_revenue),
            "avg_paid_price": float(avg_paid_price),
            "checked_in_count": checked_in_count,
            "total_stock": total_stock,
            "occupancy_rate": occupancy_rate,
            "review_count": review_count,
            "avg_score": avg_score,
        }
        provider_info = self._provider.name if self._provider else ""
        model_info = self._provider.chat_model if self._provider else ""
        summary = self._admin_chat("report_summary", context, temperature=0.4)
        return {
            "summary": summary,
            "stats": context,
            "ai_generated": bool(summary),
            "model_used": model_info,
            "provider": provider_info,
        }

    # ───────── 修复现有 "空壳" 视图：评价摘要 ─────────

    def generate_review_summary(
        self,
        *,
        hotel_id: int | None,
        start_date,
        end_date,
    ) -> dict:
        """生成评价洞察摘要（真实 LLM 调用）。"""
        import json
        from django.db.models import Avg, Count
        from apps.crm.models import Review

        qs = Review.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
            hotel = Hotel.objects.filter(id=hotel_id).first()
            hotel_scope = hotel.name if hotel else f"酒店 #{hotel_id}"
        else:
            hotel_scope = "全部酒店"

        total_reviews = qs.count()
        avg_score = round(float(qs.aggregate(avg=Avg("score"))["avg"] or 0), 2)
        score_dist = {str(i): qs.filter(score=i).count() for i in range(1, 6)}

        def extract_keywords(reviews_qs, limit=20):
            texts = list(reviews_qs.values_list("content", flat=True)[:limit])
            words = []
            for text in texts:
                words.extend(re.findall(r"[一-鿿]{2,5}", text))
            freq: dict[str, int] = {}
            for w in words:
                freq[w] = freq.get(w, 0) + 1
            stop_words = {"酒店", "房间", "服务", "非常", "很好", "不错", "感觉", "没有", "还是", "可以"}
            top = sorted(
                [(k, v) for k, v in freq.items() if k not in stop_words],
                key=lambda x: x[1],
                reverse=True,
            )
            return [k for k, _ in top[:8]]

        positive_kw = extract_keywords(qs.filter(score__gte=4))
        negative_kw = extract_keywords(qs.filter(score__lte=2))
        neutral_kw = extract_keywords(qs.filter(score=3))
        unreplied = qs.filter(reply_content="").count()

        context = {
            "hotel_scope": hotel_scope,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_reviews": total_reviews,
            "avg_score": avg_score,
            "score_distribution": json.dumps(score_dist, ensure_ascii=False),
            "positive_keywords": "、".join(positive_kw) or "（暂无）",
            "negative_keywords": "、".join(negative_kw) or "（暂无）",
            "neutral_keywords": "、".join(neutral_kw) or "（暂无）",
            "unreplied_count": unreplied,
        }
        provider_info = self._provider.name if self._provider else ""
        model_info = self._provider.chat_model if self._provider else ""
        summary = self._admin_chat("review_summary", context, temperature=0.4)
        return {
            "summary": summary,
            "stats": {
                "total_reviews": total_reviews,
                "avg_score": avg_score,
                "score_distribution": score_dist,
                "unreplied_count": unreplied,
            },
            "ai_generated": bool(summary),
            "model_used": model_info,
            "provider": provider_info,
        }

    # ───────── 修复现有 "空壳" 视图：回复建议 ─────────

    def generate_reply_suggestion(self, *, review) -> dict:
        """为评价生成 3 条回复建议（真实 LLM 调用）。"""
        hotel = review.hotel
        context = {
            "hotel_name": hotel.name if hotel else "",
            "reviewer_name": review.user.username if review.user_id else "住客",
            "score": review.score,
            "review_content": review.content,
            "has_reply": "是（已有回复，请基于改进角度生成新建议）" if review.reply_content else "否",
        }
        provider_info = self._provider.name if self._provider else ""
        model_info = self._provider.chat_model if self._provider else ""
        raw = self._admin_chat("reply_suggestion", context, temperature=0.6)
        suggestions = []
        if raw:
            blocks = re.split(r"^---+$", raw, flags=re.MULTILINE)
            for block in blocks:
                block = block.strip()
                if block:
                    m = re.match(r"^(正式风格|亲切风格|简洁风格)[：:]\s*", block)
                    if m:
                        style_label = m.group(1)
                        content = block[m.end():].strip()
                        style_map = {"正式风格": "formal", "亲切风格": "casual", "简洁风格": "concise"}
                        suggestions.append({"style": style_map.get(style_label, "formal"), "content": content})
                    else:
                        suggestions.append({"style": "formal", "content": block})
        return {
            "suggestions": suggestions,
            "raw": raw,
            "ai_generated": bool(raw),
            "model_used": model_info,
        }

    # ───────── 新功能：AI 智能定价建议 ─────────

    def generate_pricing_suggestion(
        self,
        *,
        room_type,
        target_dates: list,
        use_reasoning: bool = False,
    ) -> dict:
        """为指定房型和日期段生成 AI 定价建议。"""
        import json
        from django.utils.dateparse import parse_date
        from apps.hotels.models import RoomInventory

        hotel = room_type.hotel
        today = timezone.localdate()

        # 近 30 天历史库存数据
        history_start = today - timezone.timedelta(days=30)
        inventory_qs = RoomInventory.objects.filter(
            room_type=room_type,
            date__gte=history_start,
            date__lt=today,
        ).order_by("date")
        history_data = []
        for inv in inventory_qs:
            total = room_type.stock
            used = max(0, total - inv.stock)
            history_data.append({
                "date": str(inv.date),
                "price": float(inv.price),
                "stock": inv.stock,
                "occupancy_rate": round(used / total * 100, 1) if total else 0,
            })

        # 目标日期附加元数据
        import calendar
        CHINESE_HOLIDAYS = {
            "01-01", "02-10", "02-11", "02-12", "02-13", "02-14",
            "04-05", "05-01", "05-02", "05-03", "06-01",
            "09-29", "09-30", "10-01", "10-02", "10-03",
        }
        dates_info = []
        for d in target_dates:
            d_obj = parse_date(str(d)) if not hasattr(d, "strftime") else d
            if d_obj is None:
                continue
            mmdd = d_obj.strftime("%m-%d")
            is_holiday = mmdd in CHINESE_HOLIDAYS
            is_weekend = d_obj.weekday() >= 5
            inv = RoomInventory.objects.filter(room_type=room_type, date=d_obj).first()
            dates_info.append({
                "date": str(d_obj),
                "is_holiday": is_holiday,
                "is_weekend": is_weekend,
                "current_price": float(inv.price) if inv else float(room_type.base_price),
                "current_stock": inv.stock if inv else room_type.stock,
            })

        context = {
            "hotel_name": hotel.name,
            "room_type_name": room_type.name,
            "bed_type": room_type.get_bed_type_display(),
            "base_price": float(room_type.base_price),
            "max_guest_count": room_type.max_guest_count,
            "history_json": json.dumps(history_data, ensure_ascii=False),
            "dates_json": json.dumps(dates_info, ensure_ascii=False),
            "target_dates_str": "、".join(str(d) for d in target_dates),
        }
        raw = self._admin_chat("pricing_suggestion", context, use_reasoning=use_reasoning, temperature=0.3)
        parsed = self._parse_json_response(raw) if raw else None

        suggestions = []
        overall_analysis = ""
        if isinstance(parsed, dict):
            suggestions = parsed.get("suggestions", [])
            overall_analysis = parsed.get("overall_analysis", "")

        # 兜底：返回基础信息
        if not suggestions:
            for item in dates_info:
                suggestions.append({
                    "date": item["date"],
                    "suggested_price": item["current_price"],
                    "suggested_min": round(item["current_price"] * 0.9, 2),
                    "suggested_max": round(item["current_price"] * 1.3, 2),
                    "reason": "基于基准价估算（AI 服务不可用）",
                    "price_strategy": "standard",
                    "is_holiday": item["is_holiday"],
                    "is_weekend": item["is_weekend"],
                    "historical_occupancy_rate": None,
                })

        provider_info = self._provider.name if self._provider else ""
        model_info = (self._provider.reasoning_model if use_reasoning else self._provider.chat_model) if self._provider else ""
        return {
            "room_type_id": room_type.id,
            "room_type_name": room_type.name,
            "hotel_name": hotel.name,
            "suggestions": suggestions,
            "overall_analysis": overall_analysis,
            "ai_generated": bool(raw),
            "model_used": model_info,
        }

    # ───────── 新功能：AI 深度经营分析报告 ─────────

    def generate_business_report(
        self,
        *,
        hotel_id: int | None,
        start_date,
        end_date,
        dimensions: list | None = None,
        use_reasoning: bool = False,
    ) -> dict:
        """生成深度经营分析报告。"""
        import json
        from decimal import Decimal
        from django.db.models import Sum, Avg, Count
        from apps.bookings.models import BookingOrder
        from apps.crm.models import Review

        if dimensions is None:
            dimensions = ["revenue", "occupancy", "room_type_ranking", "review_keywords", "anomaly"]

        qs = BookingOrder.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).select_related("room_type")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
            hotel = Hotel.objects.filter(id=hotel_id).first()
            hotel_scope = hotel.name if hotel else f"酒店 #{hotel_id}"
        else:
            hotel_scope = "全部酒店"

        from datetime import date, timedelta
        import datetime as dt

        # 营收数据（按日）
        revenue_by_day = {}
        cur = start_date if isinstance(start_date, dt.date) else dt.datetime.strptime(str(start_date), "%Y-%m-%d").date()
        end_d = end_date if isinstance(end_date, dt.date) else dt.datetime.strptime(str(end_date), "%Y-%m-%d").date()
        while cur <= end_d:
            day_rev = qs.filter(created_at__date=cur, payment_status=BookingOrder.PAYMENT_PAID).aggregate(
                total=Sum("pay_amount")
            )["total"] or Decimal(0)
            revenue_by_day[str(cur)] = float(day_rev)
            cur += timedelta(days=1)

        total_revenue = sum(revenue_by_day.values())
        total_orders = qs.count()
        paid_orders = qs.filter(payment_status=BookingOrder.PAYMENT_PAID).count()
        cancelled_orders = qs.filter(status=BookingOrder.STATUS_CANCELLED).count()

        # 房型排名
        room_ranking = []
        if "room_type_ranking" in dimensions:
            rt_data = (
                qs.filter(payment_status=BookingOrder.PAYMENT_PAID)
                .values("room_type__name")
                .annotate(revenue=Sum("pay_amount"), count=Count("id"))
                .order_by("-revenue")[:8]
            )
            for item in rt_data:
                room_ranking.append({
                    "name": item["room_type__name"],
                    "order_count": item["count"],
                    "revenue": float(item["revenue"] or 0),
                })

        # 评价数据
        review_qs = Review.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        if hotel_id:
            review_qs = review_qs.filter(hotel_id=hotel_id)
        avg_score = round(float(review_qs.aggregate(avg=Avg("score"))["avg"] or 0), 2)
        review_count = review_qs.count()

        def top_words(reviews_qs, n=6):
            texts = list(reviews_qs.values_list("content", flat=True)[:30])
            freq: dict[str, int] = {}
            for text in texts:
                for w in re.findall(r"[一-鿿]{2,5}", text):
                    freq[w] = freq.get(w, 0) + 1
            stop = {"酒店", "房间", "非常", "很好", "感觉", "没有", "还是", "可以", "不错"}
            top = sorted([(k, v) for k, v in freq.items() if k not in stop], key=lambda x: -x[1])
            return [k for k, _ in top[:n]]

        positive_kw = top_words(review_qs.filter(score__gte=4))
        negative_kw = top_words(review_qs.filter(score__lte=2))

        # 异常标记
        occupancy = round(
            BookingOrder.objects.filter(status=BookingOrder.STATUS_CHECKED_IN).count()
            / max(1, RoomType.objects.aggregate(s=Sum("stock"))["s"] or 1) * 100, 1
        )
        anomaly_flags = []
        cancel_rate = round(cancelled_orders / max(1, total_orders) * 100, 1)
        if cancel_rate > 30:
            anomaly_flags.append(f"取消率 {cancel_rate}% 偏高（阈值 30%）")
        if avg_score < 3.5 and review_count > 0:
            anomaly_flags.append(f"平均评分 {avg_score} 偏低（阈值 3.5 分）")

        context = {
            "hotel_scope": hotel_scope,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "dimensions_str": "、".join(dimensions),
            "has_anomaly": bool(anomaly_flags),
            "revenue_data_json": json.dumps({
                "total_revenue": total_revenue,
                "daily": revenue_by_day,
            }, ensure_ascii=False),
            "order_data_json": json.dumps({
                "total_orders": total_orders,
                "paid_orders": paid_orders,
                "cancelled_orders": cancelled_orders,
                "cancel_rate": cancel_rate,
                "occupancy_rate": occupancy,
            }, ensure_ascii=False),
            "room_type_ranking_json": json.dumps(room_ranking, ensure_ascii=False),
            "review_data_json": json.dumps({
                "total_reviews": review_count,
                "avg_score": avg_score,
                "positive_keywords": positive_kw,
                "negative_keywords": negative_kw,
            }, ensure_ascii=False),
            "anomaly_flags_json": json.dumps(anomaly_flags, ensure_ascii=False),
        }
        raw = self._admin_chat("business_report", context, use_reasoning=use_reasoning, temperature=0.4)
        provider_info = self._provider.name if self._provider else ""
        model_info = (self._provider.reasoning_model if use_reasoning else self._provider.chat_model) if self._provider else ""
        return {
            "report_markdown": raw or "（AI 服务不可用，无法生成报告）",
            "summary": (raw or "")[:200] if raw else "",
            "highlights": [
                {"type": "info", "text": f"统计区间总营收 ¥{total_revenue:.2f}"},
                {"type": "info", "text": f"共 {total_orders} 笔订单，取消率 {cancel_rate}%"},
            ],
            "ai_generated": bool(raw),
            "model_used": model_info,
        }

    def stream_business_report(
        self,
        *,
        hotel_id: int | None,
        start_date,
        end_date,
        dimensions: list | None = None,
        use_reasoning: bool = False,
    ):
        """流式生成经营分析报告（返回 OpenAI stream 迭代器或 fallback 文本）。"""
        import json
        from decimal import Decimal
        from django.db.models import Sum
        from apps.bookings.models import BookingOrder
        if dimensions is None:
            dimensions = ["revenue", "occupancy", "room_type_ranking", "review_keywords"]

        qs = BookingOrder.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
            hotel = Hotel.objects.filter(id=hotel_id).first()
            hotel_scope = hotel.name if hotel else f"酒店 #{hotel_id}"
        else:
            hotel_scope = "全部酒店"

        total_orders = qs.count()
        total_revenue = float(
            qs.filter(payment_status=BookingOrder.PAYMENT_PAID).aggregate(total=Sum("pay_amount"))["total"] or Decimal(0)
        )
        cancel_rate = round(
            qs.filter(status=BookingOrder.STATUS_CANCELLED).count() / max(1, total_orders) * 100, 1
        )
        from apps.crm.models import Review
        review_qs = Review.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        if hotel_id:
            review_qs = review_qs.filter(hotel_id=hotel_id)

        context = {
            "hotel_scope": hotel_scope,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "dimensions_str": "、".join(dimensions),
            "has_anomaly": cancel_rate > 30,
            "revenue_data_json": json.dumps({"total_revenue": total_revenue}, ensure_ascii=False),
            "order_data_json": json.dumps({"total_orders": total_orders, "cancel_rate": cancel_rate}, ensure_ascii=False),
            "room_type_ranking_json": "[]",
            "review_data_json": json.dumps({"total_reviews": review_qs.count()}, ensure_ascii=False),
            "anomaly_flags_json": "[]",
        }

        if not self.is_available():
            return None, "（AI 服务不可用，无法生成报告）"

        system_prompt = self.prompt_service.render_admin("business_report", "system", **context)
        user_prompt = self.prompt_service.render_admin("business_report", "user", **context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        model = None
        if use_reasoning and self._provider and self._provider.reasoning_model:
            model = self._provider.reasoning_model
        stream = self.stream_chat_completion(messages, model=model, temperature=0.4)
        return stream, None

    # ───────── 新功能：AI 营销文案生成 ─────────

    def generate_marketing_copy(
        self,
        *,
        hotel_id: int | None,
        copy_type: str,
        style: str = "formal",
        keywords: list | None = None,
        target_audience: str = "",
        extra_notes: str = "",
    ) -> dict:
        """生成营销文案。"""
        import json
        hotel = Hotel.objects.filter(id=hotel_id).first() if hotel_id else None
        room_highlights = []
        if hotel:
            for rt in RoomType.objects.filter(hotel=hotel, status=RoomType.STATUS_ONLINE)[:3]:
                room_highlights.append(f"{rt.name}（¥{rt.base_price}/晚）")

        context = {
            "hotel_name": hotel.name if hotel else "HoteLink 酒店",
            "city": hotel.city if hotel else "",
            "star": hotel.star if hotel else 4,
            "address": hotel.address if hotel else "",
            "description": (hotel.description or "")[:200] if hotel else "",
            "min_price": float(hotel.min_price) if hotel else 0,
            "room_highlights": "、".join(room_highlights) or "（暂无房型数据）",
            "copy_type": copy_type,
            "styles_str": style,
            "keywords_str": "、".join(keywords or []) or "（未指定）",
            "target_audience": target_audience or "通用",
            "extra_notes": extra_notes or "（无额外要求）",
        }
        raw = self._admin_chat("marketing_copy", context, temperature=0.7)
        parsed = self._parse_json_response(raw) if raw else None

        copies = []
        if isinstance(parsed, dict) and "copies" in parsed:
            copies = parsed["copies"]
        elif not copies:
            copies = [{"title": "精品体验", "content": raw or "AI 服务暂不可用", "style": style}]

        provider_info = self._provider.name if self._provider else ""
        return {
            "copies": copies,
            "ai_generated": bool(raw),
            "provider": provider_info,
        }

    # ───────── 新功能：AI 内容生成助手 ─────────

    def generate_content(
        self,
        *,
        content_type: str,
        context_data: dict,
        count: int = 3,
    ) -> dict:
        """生成酒店/房型描述或 SEO 关键词。"""
        import json
        context = {
            "content_type": content_type,
            "count": count,
            "context_json": json.dumps(context_data, ensure_ascii=False),
        }
        raw = self._admin_chat("content_generate", context, temperature=0.7)
        parsed = self._parse_json_response(raw) if raw else None

        candidates = []
        if isinstance(parsed, dict) and "candidates" in parsed:
            candidates = parsed["candidates"]
        elif isinstance(parsed, list):
            candidates = parsed
        elif raw:
            candidates = [raw]

        provider_info = self._provider.name if self._provider else ""
        return {
            "candidates": candidates[:count],
            "ai_generated": bool(raw),
            "provider": provider_info,
        }

    # ───────── 新功能：AI 评价情感分析 ─────────

    def analyze_review_sentiment(self, *, review) -> dict:
        """分析单条评价的情感、关键词和标签。"""
        hotel = review.hotel
        context = {
            "hotel_name": hotel.name if hotel else "",
            "score": review.score,
            "review_content": review.content,
        }
        raw = self._admin_chat("review_sentiment", context, temperature=0.2)
        parsed = self._parse_json_response(raw) if raw else None

        if isinstance(parsed, dict):
            return {
                "review_id": review.id,
                "sentiment_score": float(parsed.get("sentiment_score", 0.5)),
                "sentiment_label": parsed.get("sentiment_label", "neutral"),
                "keywords": parsed.get("keywords", []),
                "tags": parsed.get("tags", []),
                "summary": parsed.get("summary", ""),
                "ai_generated": True,
            }

        # 兜底：基于评分
        score = review.score
        if score >= 4:
            label, score_val = "positive", 0.8
        elif score == 3:
            label, score_val = "neutral", 0.5
        else:
            label, score_val = "negative", 0.2
        return {
            "review_id": review.id,
            "sentiment_score": score_val,
            "sentiment_label": label,
            "keywords": [],
            "tags": [],
            "summary": "",
            "ai_generated": False,
        }

    # ───────── 新功能：AI 异常检测报告 ─────────

    def generate_anomaly_report(
        self,
        *,
        hotel_id: int | None,
        analysis_date,
    ) -> dict:
        """生成今日运营异常报告。"""
        import json
        from apps.bookings.models import BookingOrder
        from apps.crm.models import Review
        from django.db.models import Sum

        today = analysis_date
        yesterday = today - timezone.timedelta(days=1)

        qs_base = BookingOrder.objects
        if hotel_id:
            qs_base = qs_base.filter(hotel_id=hotel_id)
            hotel = Hotel.objects.filter(id=hotel_id).first()
            hotel_scope = hotel.name if hotel else f"酒店 #{hotel_id}"
        else:
            hotel_scope = "全部酒店"

        today_new = qs_base.filter(created_at__date=today).count()
        today_cancelled = qs_base.filter(created_at__date=today, status=BookingOrder.STATUS_CANCELLED).count()
        today_cancel_rate = round(today_cancelled / max(1, today_new) * 100, 1)
        today_checked_in = qs_base.filter(status=BookingOrder.STATUS_CHECKED_IN).count()
        today_expected = qs_base.filter(check_in_date=today, status__in=[
            BookingOrder.STATUS_CONFIRMED, BookingOrder.STATUS_PAID
        ]).count()

        total_stock = RoomType.objects.aggregate(s=Sum("stock"))["s"] or 1
        today_occ = round(today_checked_in / total_stock * 100, 1)

        yesterday_checked_in = qs_base.filter(
            status=BookingOrder.STATUS_CHECKED_IN,
        ).count()
        # 用昨日 check_in_date 订单近似昨日在住率
        yesterday_occ = today_occ  # fallback

        overdue_checkin_qs = qs_base.filter(
            check_in_date__lt=today,
            status__in=[BookingOrder.STATUS_CONFIRMED, BookingOrder.STATUS_PAID],
        )
        overdue_checkout_qs = qs_base.filter(
            check_out_date__lt=today,
            status=BookingOrder.STATUS_CHECKED_IN,
        )
        overdue_checkin_ids = list(overdue_checkin_qs.values_list("id", flat=True)[:10])
        overdue_checkout_ids = list(overdue_checkout_qs.values_list("id", flat=True)[:10])

        recent_reviews = Review.objects.filter(created_at__date__gte=today - timezone.timedelta(days=1))
        if hotel_id:
            recent_reviews = recent_reviews.filter(hotel_id=hotel_id)
        positive_count = recent_reviews.filter(score__gte=4).count()
        neutral_count = recent_reviews.filter(score=3).count()
        negative_count = recent_reviews.filter(score__lte=2).count()
        neg_summaries = list(
            recent_reviews.filter(score__lte=2).values_list("content", flat=True)[:3]
        )

        context = {
            "analysis_date": str(today),
            "hotel_scope": hotel_scope,
            "today_new_orders": today_new,
            "today_cancelled": today_cancelled,
            "today_cancel_rate": today_cancel_rate,
            "today_checked_in": today_checked_in,
            "today_expected_checkin": today_expected,
            "today_occupancy_rate": today_occ,
            "yesterday_occupancy_rate": yesterday_occ,
            "occupancy_drop": max(0, round(yesterday_occ - today_occ, 1)),
            "overdue_checkin_count": overdue_checkin_qs.count(),
            "overdue_checkin_ids": json.dumps(overdue_checkin_ids),
            "overdue_checkout_count": overdue_checkout_qs.count(),
            "overdue_checkout_ids": json.dumps(overdue_checkout_ids),
            "recent_positive_count": positive_count,
            "recent_neutral_count": neutral_count,
            "recent_negative_count": negative_count,
            "negative_review_summaries": "；".join(neg_summaries[:3]) or "（无差评）",
        }

        raw = self._admin_chat("anomaly_report", context, temperature=0.3)
        parsed = self._parse_json_response(raw) if raw else None

        if isinstance(parsed, dict):
            return {
                "date": str(today),
                "hotel_id": hotel_id,
                "has_anomaly": parsed.get("has_anomaly", False),
                "anomalies": parsed.get("anomalies", []),
                "overall_status": parsed.get("overall_status", "normal"),
                "ai_generated": True,
            }

        # 兜底：规则生成异常列表
        anomalies = []
        if overdue_checkin_qs.count() > 0:
            anomalies.append({
                "type": "overdue_checkin",
                "severity": "warning",
                "title": f"{overdue_checkin_qs.count()} 单入住日期已过未入住",
                "description": f"订单 {overdue_checkin_ids[:5]} 超过入住日期仍未办理入住",
                "ai_analysis": "建议联系客户确认是否需要取消",
                "suggested_actions": ["联系客户确认", "考虑取消超期未入住订单"],
            })
        if overdue_checkout_qs.count() > 0:
            anomalies.append({
                "type": "overdue_checkout",
                "severity": "warning",
                "title": f"{overdue_checkout_qs.count()} 单退房日期已过未退房",
                "description": f"订单 {overdue_checkout_ids[:5]} 超过退房日期仍未退房",
                "ai_analysis": "建议前台主动确认退房情况",
                "suggested_actions": ["前台确认入住状态", "处理超期账单"],
            })
        if negative_count >= 3:
            anomalies.append({
                "type": "negative_review_spike",
                "severity": "danger" if negative_count >= 5 else "warning",
                "title": f"近24小时内 {negative_count} 条差评",
                "description": f"差评内容: {neg_summaries[0][:50] if neg_summaries else '（无内容）'}",
                "ai_analysis": "差评集中爆发，请及时关注并回复",
                "suggested_actions": ["主动联系差评客户致歉", "排查共性问题"],
            })
        return {
            "date": str(today),
            "hotel_id": hotel_id,
            "has_anomaly": bool(anomalies),
            "anomalies": anomalies,
            "overall_status": "critical" if any(a["severity"] == "danger" for a in anomalies) else (
                "warning" if anomalies else "normal"
            ),
            "ai_generated": False,
        }

    # ───────── 新功能：AI 订单异常摘要 ─────────

    def generate_order_anomaly_summary(self, *, analysis_date) -> dict:
        """生成今日订单异常摘要（规则驱动 + AI 解释）。"""
        from apps.bookings.models import BookingOrder
        from django.db.models import Count

        today = analysis_date
        anomalies = []

        # 超时未支付（超过60分钟的 pending_payment 订单）
        overdue_payment_cutoff = timezone.now() - timezone.timedelta(minutes=60)
        overdue_payment = BookingOrder.objects.filter(
            status=BookingOrder.STATUS_PENDING_PAYMENT,
            created_at__lt=overdue_payment_cutoff,
        )
        if overdue_payment.exists():
            ids = list(overdue_payment.values_list("id", flat=True)[:10])
            anomalies.append({
                "type": "overdue_payment",
                "count": overdue_payment.count(),
                "description": f"{overdue_payment.count()} 个订单超过 60 分钟未支付",
                "order_ids": ids,
                "suggestion": "建议发送支付提醒通知，或取消超时未支付订单",
            })

        # 频繁取消用户（7天内取消3次以上）
        week_ago = today - timezone.timedelta(days=7)
        frequent_cancel_users = (
            BookingOrder.objects.filter(
                status=BookingOrder.STATUS_CANCELLED,
                created_at__date__gte=week_ago,
            )
            .values("user_id")
            .annotate(cancel_count=Count("id"))
            .filter(cancel_count__gte=3)
        )
        if frequent_cancel_users.exists():
            user_ids = [item["user_id"] for item in frequent_cancel_users[:5]]
            anomalies.append({
                "type": "frequent_cancel_user",
                "count": frequent_cancel_users.count(),
                "description": f"{frequent_cancel_users.count()} 个用户近 7 天内取消 3 次以上",
                "user_ids": user_ids,
                "suggestion": "建议关注高频取消用户行为，评估是否限制预订",
            })

        # 入住日期已过未入住
        overdue_checkin = BookingOrder.objects.filter(
            check_in_date__lt=today,
            status__in=[BookingOrder.STATUS_CONFIRMED, BookingOrder.STATUS_PAID],
        )
        if overdue_checkin.exists():
            ids = list(overdue_checkin.values_list("id", flat=True)[:10])
            anomalies.append({
                "type": "overdue_checkin",
                "count": overdue_checkin.count(),
                "description": f"{overdue_checkin.count()} 个已确认订单入住日期已过但未入住",
                "order_ids": ids,
                "suggestion": "建议联系客户确认是否取消",
            })

        summary = f"今日共检测到 {len(anomalies)} 类异常，涉及 {sum(a['count'] for a in anomalies)} 个事项"
        return {
            "date": str(today),
            "summary": summary,
            "anomalies": anomalies,
            "ai_generated": False,
        }

    # ───────── 新功能：AI 智能推荐 ─────────

    def generate_recommendations(
        self,
        *,
        user,
        scene: str = "home",
        hotel_id: int | None = None,
        keyword: str | None = None,
        limit: int = 6,
    ) -> list[dict]:
        """为用户生成个性化酒店推荐。"""
        import json
        from apps.bookings.models import BookingOrder
        from apps.crm.models import FavoriteHotel

        # 构建用户历史画像
        recent_orders = BookingOrder.objects.filter(user=user).select_related("hotel").order_by("-id")[:10]
        favorite_hotel_ids = list(FavoriteHotel.objects.filter(user=user).values_list("hotel_id", flat=True)[:20])

        preferred_cities = list({o.hotel.city for o in recent_orders if o.hotel})
        preferred_stars = list({o.hotel.star for o in recent_orders if o.hotel})
        total_spent = float(sum(o.pay_amount for o in recent_orders))

        user_profile = {
            "order_count": len(recent_orders),
            "total_spent": total_spent,
            "preferred_cities": preferred_cities,
            "preferred_stars": preferred_stars,
            "favorite_hotels": favorite_hotel_ids[:10],
        }

        # 候选酒店（排除已订近期酒店，优先在线酒店）
        exclude_ids = [o.hotel_id for o in recent_orders if o.hotel_id]
        candidates = Hotel.objects.filter(status=Hotel.STATUS_ONLINE)
        if scene == "hotel_detail" and hotel_id:
            target = Hotel.objects.filter(id=hotel_id).first()
            if target:
                candidates = candidates.filter(city=target.city).exclude(id=hotel_id)
        elif scene == "search" and keyword:
            candidates = candidates.filter(
                name__icontains=keyword
            ) | candidates.filter(city__icontains=keyword)
        candidates = candidates.order_by("-rating", "-id")[:20]

        hotels_data = [
            {
                "id": h.id,
                "name": h.name,
                "city": h.city,
                "star": h.star,
                "rating": float(h.rating),
                "min_price": float(h.min_price),
                "is_recommended": h.is_recommended,
            }
            for h in candidates
        ]

        context = {
            "user_profile_json": json.dumps(user_profile, ensure_ascii=False),
            "hotels_json": json.dumps(hotels_data, ensure_ascii=False),
            "scene": scene,
            "keyword": keyword or "",
            "limit": limit,
        }

        raw = self._admin_chat("recommendations", context, temperature=0.4)
        parsed = self._parse_json_response(raw) if raw else None

        recommended_ids = []
        reasons: dict[str, str] = {}
        if isinstance(parsed, dict):
            recommended_ids = [int(i) for i in parsed.get("recommended_ids", [])]
            reasons = {str(k): v for k, v in parsed.get("reasons", {}).items()}

        if not recommended_ids:
            recommended_ids = [h["id"] for h in hotels_data[:limit]]

        hotel_map = {h.id: h for h in candidates}
        result = []
        for hid in recommended_ids[:limit]:
            hotel = hotel_map.get(hid)
            if hotel is None:
                continue
            reason = reasons.get(str(hid), "根据您的偏好推荐")
            result.append({
                "hotel_id": hotel.id,
                "hotel_name": hotel.name,
                "city": hotel.city,
                "star": hotel.star,
                "rating": float(hotel.rating),
                "min_price": float(hotel.min_price),
                "cover_image": hotel.cover_image or "",
                "recommendation_reason": reason,
            })
        return result

    # ───────── 新功能：AI 酒店对比分析 ─────────

    def generate_hotel_compare(
        self,
        *,
        hotel_ids: list[int],
        check_in_date=None,
        check_out_date=None,
    ) -> dict:
        """对多家酒店进行 AI 对比分析。"""
        import json
        hotels = list(Hotel.objects.filter(id__in=hotel_ids).prefetch_related("room_types"))
        if not hotels:
            return {"hotels": [], "ai_summary": "未找到指定酒店", "ai_generated": False}

        hotels_data = []
        for hotel in hotels:
            rts = list(hotel.room_types.filter(status=RoomType.STATUS_ONLINE).order_by("base_price")[:3])
            hotels_data.append({
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
                        "name": rt.name,
                        "bed_type": rt.get_bed_type_display(),
                        "area": rt.area,
                        "price": float(rt.base_price),
                    }
                    for rt in rts
                ],
            })

        context = {
            "check_in_date": str(check_in_date) if check_in_date else "",
            "check_out_date": str(check_out_date) if check_out_date else "",
            "hotels_json": json.dumps(hotels_data, ensure_ascii=False),
        }
        raw = self._admin_chat("hotel_compare", context, temperature=0.4)
        parsed = self._parse_json_response(raw) if raw else None

        hotel_analysis = []
        ai_summary = ""
        recommendation = ""
        if isinstance(parsed, dict):
            hotel_analysis = parsed.get("hotel_analysis", [])
            ai_summary = parsed.get("comparison_summary", "")
            recommendation = parsed.get("recommendation", "")

        if not hotel_analysis:
            for h in hotels:
                hotel_analysis.append({
                    "hotel_id": h.id,
                    "strengths": [f"{h.star}星级"],
                    "weaknesses": [],
                    "suitable_for": "通用",
                })

        # 合并 AI 分析和原始酒店数据
        final_hotels = []
        for hdata in hotels_data:
            analysis = next((a for a in hotel_analysis if a.get("hotel_id") == hdata["id"]), {})
            final_hotels.append({
                **hdata,
                "strengths": analysis.get("strengths", []),
                "weaknesses": analysis.get("weaknesses", []),
                "suitable_for": analysis.get("suitable_for", "通用"),
            })

        return {
            "hotels": final_hotels,
            "ai_summary": ai_summary,
            "recommendation": recommendation,
            "ai_generated": bool(raw),
        }
