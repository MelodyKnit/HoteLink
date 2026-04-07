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
from apps.hotels.models import Hotel, RoomType
from apps.operations.models import SystemNotice
from apps.operations.services.prompt_service import PromptSceneError, PromptTemplateService, SUPPORTED_CUSTOMER_SERVICE_TOPICS
from config.ai import AIProviderConfig, build_ai_client, load_ai_settings

logger = logging.getLogger(__name__)


class AIChatService:
    """AI 对话服务封装，支持多供应商切换、提示词渲染与上下文绑定。"""

    BOOKING_INTENT_KEYWORDS = (
        "订酒店",
        "想订",
        "选酒店",
        "找酒店",
        "预订",
        "订房",
        "订个房",
        "订",
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
            requested_scene=scene,
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

        system_prompt = (
            "你是酒店预订意图解析器。请从用户输入中提取订房结构化字段，并且只输出 JSON。"
            "字段: selected_city(字符串或null), hotel_keyword(字符串或null), reset(布尔), switch_hotel(布尔),"
            " sort_by(可选:price_asc/rating_desc/price_desc/null), budget_max(整数或null), min_rating(数字或null), nearby_radius_km(整数或null)。"
            "reset 用于表达‘重新开始/重选城市’，switch_hotel 用于表达‘换一家/不要这个酒店’。"
        )
        user_prompt = (
            f"可选城市: {', '.join(cities)}\n"
            f"用户输入: {question}\n"
            "只返回 JSON，不要解释。"
        )
        try:
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
                "selected_city": payload.get("selected_city") or None,
                "hotel_keyword": payload.get("hotel_keyword") or None,
                "reset": bool(payload.get("reset", False)),
                "switch_hotel": bool(payload.get("switch_hotel", False)),
                "sort_by": payload.get("sort_by") or None,
                "budget_max": payload.get("budget_max"),
                "min_rating": payload.get("min_rating"),
                "nearby_radius_km": payload.get("nearby_radius_km"),
            }
        except Exception:
            return {}

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
