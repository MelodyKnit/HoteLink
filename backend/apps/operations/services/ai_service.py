"""apps/operations/services/ai_service.py —— AI 对话服务封装（多模型支持）。"""

from __future__ import annotations

import logging
from collections.abc import Iterator
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

    BOOKING_INTENT_KEYWORDS = (
        "订酒店",
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
    BOOKING_RESET_KEYWORDS = ("重新订", "重选", "换个城市", "重新开始", "重新选", "换一家")

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

    def reply_customer_service(
        self,
        *,
        user: Any,
        scene: str,
        question: str,
        hotel_id: int | None = None,
        order_id: int | None = None,
        booking_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_scene = self.normalize_scene(scene)
        booking_assistant = self._build_booking_assistant_response(
            user=user,
            question=question,
            hotel_id=hotel_id,
            booking_context=booking_context,
        )
        if booking_assistant is not None:
            return {
                "scene": normalized_scene,
                "answer": booking_assistant["answer"],
                "booking_assistant": booking_assistant,
            }

        _, messages = self.build_customer_service_messages(
            user=user,
            scene=normalized_scene,
            question=question,
            hotel_id=hotel_id,
            order_id=order_id,
        )

        try:
            if self.is_available():
                result = self.create_chat_completion(messages, temperature=0.2)
                answer = result["content"]
            else:
                answer = ""
        except Exception:
            answer = ""

        return {
            "scene": normalized_scene,
            "answer": answer,
            "booking_assistant": None,
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

    def _build_booking_assistant_response(
        self,
        *,
        user: Any,
        question: str,
        hotel_id: int | None,
        booking_context: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        context = self._normalize_booking_context(booking_context)
        if self._should_reset_booking_context(question):
            context = {"intent": "hotel_booking", "selected_city": None, "selected_hotel_id": None}

        if not self._should_enter_booking_flow(question, hotel_id=hotel_id, booking_context=context):
            return None

        cities = self._list_available_cities()
        selected_city = context.get("selected_city") or self._extract_city_from_question(question, cities)
        matched_hotel = self._resolve_hotel_from_booking_context(
            question=question,
            hotel_id=hotel_id,
            selected_city=selected_city,
            booking_context=context,
        )

        if isinstance(matched_hotel, list):
            options = [self._build_hotel_option(item) for item in matched_hotel[:6]]
            answer = "我识别到您提到了多个可预订酒店，先点一个酒店，我直接带您看该酒店可下单的房型。"
            return {
                "intent": "hotel_booking",
                "phase": "select_hotel",
                "context": {
                    "intent": "hotel_booking",
                    "selected_city": selected_city,
                    "selected_hotel_id": None,
                },
                "options": options,
                "answer": answer,
            }

        if matched_hotel is not None:
            room_types = list(
                RoomType.objects.filter(hotel=matched_hotel, status=RoomType.STATUS_ONLINE).order_by("base_price", "id")[:8]
            )
            answer = self._build_room_type_answer(matched_hotel, room_types)
            return {
                "intent": "hotel_booking",
                "phase": "select_room_type",
                "context": {
                    "intent": "hotel_booking",
                    "selected_city": matched_hotel.city,
                    "selected_hotel_id": matched_hotel.id,
                },
                "options": [self._build_room_type_option(matched_hotel, room_type) for room_type in room_types],
                "answer": answer,
            }

        if selected_city:
            hotels = list(
                Hotel.objects.filter(city=selected_city, status=Hotel.STATUS_ONLINE).order_by("-is_recommended", "-rating", "min_price", "id")[:8]
            )
            if hotels:
                answer = f"已为您切到{selected_city}，这里有 {len(hotels)} 家当前可预订酒店。点一家，我继续把房型直接展开给您。"
                return {
                    "intent": "hotel_booking",
                    "phase": "select_hotel",
                    "context": {
                        "intent": "hotel_booking",
                        "selected_city": selected_city,
                        "selected_hotel_id": None,
                    },
                    "options": [self._build_hotel_option(hotel) for hotel in hotels],
                    "answer": answer,
                }

            answer = f"{selected_city} 暂时没有可预订酒店，您可以换一个城市，我把当前系统里可选城市都列给您。"
            return {
                "intent": "hotel_booking",
                "phase": "select_city",
                "context": {
                    "intent": "hotel_booking",
                    "selected_city": None,
                    "selected_hotel_id": None,
                },
                "options": [self._build_city_option(city) for city in cities[:12]],
                "answer": answer,
            }

        answer = "可以，我来帮您直接订酒店。先选城市，我只展示系统里当前可预订的城市，您点一下我就继续带您选酒店。"
        return {
            "intent": "hotel_booking",
            "phase": "select_city",
            "context": {
                "intent": "hotel_booking",
                "selected_city": None,
                "selected_hotel_id": None,
            },
            "options": [self._build_city_option(city) for city in cities[:12]],
            "answer": answer,
        }

    def _should_enter_booking_flow(
        self,
        question: str,
        *,
        hotel_id: int | None,
        booking_context: dict[str, Any],
    ) -> bool:
        if hotel_id or booking_context.get("selected_hotel_id") or booking_context.get("selected_city"):
            return True
        if booking_context.get("intent") == "hotel_booking":
            return True
        if any(keyword in question for keyword in self.BOOKING_INTENT_KEYWORDS):
            return True
        return self._question_mentions_known_hotel(question)

    def _should_reset_booking_context(self, question: str) -> bool:
        return any(keyword in question for keyword in self.BOOKING_RESET_KEYWORDS)

    def _normalize_booking_context(self, booking_context: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(booking_context, dict):
            return {}
        selected_hotel_id = booking_context.get("selected_hotel_id")
        try:
            selected_hotel_id = int(selected_hotel_id) if selected_hotel_id else None
        except (TypeError, ValueError):
            selected_hotel_id = None
        selected_city = booking_context.get("selected_city") or None
        return {
            "intent": booking_context.get("intent") or None,
            "selected_city": selected_city,
            "selected_hotel_id": selected_hotel_id,
        }

    def _list_available_cities(self) -> list[str]:
        return list(Hotel.objects.filter(status=Hotel.STATUS_ONLINE).exclude(city="").values_list("city", flat=True).distinct().order_by("city"))

    def _extract_city_from_question(self, question: str, cities: list[str]) -> str | None:
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
    ) -> Hotel | list[Hotel] | None:
        target_hotel_id = hotel_id or booking_context.get("selected_hotel_id")
        if target_hotel_id:
            return Hotel.objects.filter(id=target_hotel_id, status=Hotel.STATUS_ONLINE).first()

        queryset = Hotel.objects.filter(status=Hotel.STATUS_ONLINE)
        if selected_city:
            queryset = queryset.filter(city=selected_city)
        candidates = list(queryset.order_by("-is_recommended", "-rating", "min_price", "id")[:20])
        matched = [hotel for hotel in candidates if hotel.name and hotel.name in question]
        if len(matched) == 1:
            return matched[0]
        if len(matched) > 1:
            return matched
        return None

    def _question_mentions_known_hotel(self, question: str) -> bool:
        if not question.strip():
            return False
        hotels = Hotel.objects.filter(status=Hotel.STATUS_ONLINE).values_list("name", flat=True)[:50]
        return any(name and name in question for name in hotels)

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

    def _build_hotel_option(self, hotel: Hotel) -> dict[str, Any]:
        return {
            "type": "select_hotel",
            "label": hotel.name,
            "value": str(hotel.id),
            "description": f"{hotel.city} | {hotel.star}星 | 评分{hotel.rating} | ¥{hotel.min_price}起",
            "payload": {
                "intent": "hotel_booking",
                "selected_city": hotel.city,
                "selected_hotel_id": hotel.id,
            },
        }

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
