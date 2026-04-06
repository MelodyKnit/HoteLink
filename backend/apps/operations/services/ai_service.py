"""apps/operations/services/ai_service.py —— AI 对话服务封装（多模型支持）。"""

from __future__ import annotations

import logging
from typing import Any

from django.utils import timezone

from apps.bookings.models import BookingOrder
from apps.hotels.models import Hotel, RoomType
from apps.operations.models import SystemNotice
from apps.operations.services.prompt_service import PromptSceneError, PromptTemplateService, SUPPORTED_CUSTOMER_SERVICE_TOPICS
from config.ai import AIProviderConfig, build_ai_client, load_ai_settings

logger = logging.getLogger(__name__)


class AIChatService:
    """AI 对话服务封装，支持多供应商切换、提示词渲染与上下文绑定。"""

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
        return self.prompt_service.normalize_scene(scene)

    def build_customer_service_messages(
        self,
        *,
        user: Any,
        scene: str,
        question: str,
        hotel_id: int | None = None,
        order_id: int | None = None,
    ) -> tuple[str, list[dict[str, str]]]:
        normalized_scene = self.normalize_scene(scene)
        if normalized_scene != "customer_service":
            raise PromptSceneError(f"unsupported AI scene: {scene}")

        prompt_context = self._build_customer_service_prompt_context(
            user=user,
            hotel_id=hotel_id,
            order_id=order_id,
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
        return normalized_scene, messages

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

        recent_orders = [self._serialize_order(item) for item in user_orders[:5]]
        recommended_hotels = [
            self._serialize_hotel(item)
            for item in Hotel.objects.filter(status=Hotel.STATUS_ONLINE, is_recommended=True).order_by("-updated_at", "-id")[:5]
        ]
        recent_notices = [
            self._serialize_notice(item)
            for item in SystemNotice.objects.filter(user=user).order_by("-created_at", "-id")[:5]
        ]

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
