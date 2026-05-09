"""Payment orchestration helpers shared by API views."""

from __future__ import annotations

from typing import Any

from apps.bookings.models import BookingOrder
from config.payment import PAYMENT_SCENE_LABELS, PaymentGatewayConfig, load_payment_settings


PAYMENT_METHOD_PRESENTATION: dict[str, dict[str, str]] = {
    "mock": {
        "label": "模拟支付",
        "description": "用于演示、联调或课堂验收，可在管理端关闭。",
        "icon": "💳",
    },
    "wechat": {
        "label": "微信支付",
        "description": "支持 JSAPI、H5、Native 等微信支付场景。",
        "icon": "💚",
    },
    "alipay": {
        "label": "支付宝",
        "description": "支持电脑网站支付、手机网站支付等支付宝场景。",
        "icon": "🔵",
    },
    "custom": {
        "label": "其它支付平台",
        "description": "适用于聚合支付、银联或企业自有支付平台。",
        "icon": "🪙",
    },
}


def build_user_payment_methods() -> list[dict[str, Any]]:
    """Return user-facing payment method options from runtime settings."""

    settings = load_payment_settings()
    items: list[dict[str, Any]] = []

    if settings.mock_enabled:
        meta = PAYMENT_METHOD_PRESENTATION["mock"]
        items.append(
            {
                "value": "mock",
                "label": meta["label"],
                "description": meta["description"],
                "icon": meta["icon"],
                "gateway_name": "mock",
                "gateway_label": meta["label"],
                "provider_type": "mock",
                "payment_method": "mock",
                "scene": "mock",
                "scenes": ["mock"],
                "sandbox": True,
                "action_type": "mock_success",
                "is_mock": True,
            }
        )

    for gateway in settings.list_available_gateways():
        meta = PAYMENT_METHOD_PRESENTATION.get(gateway.payment_method, PAYMENT_METHOD_PRESENTATION["custom"])
        scene_label = PAYMENT_SCENE_LABELS.get(gateway.primary_scene, gateway.primary_scene or "支付")
        description = gateway.description or meta["description"]
        if gateway.primary_scene:
            description = f"{description} 当前主场景：{scene_label}。"
        items.append(
            {
                "value": gateway.payment_method,
                "label": gateway.label or meta["label"],
                "description": description,
                "icon": meta["icon"],
                "gateway_name": gateway.name,
                "gateway_label": gateway.label or meta["label"],
                "provider_type": gateway.provider_type,
                "payment_method": gateway.payment_method,
                "scene": gateway.primary_scene,
                "scenes": gateway.normalized_scenes,
                "sandbox": gateway.sandbox,
                "action_type": gateway.action_type_hint,
                "is_mock": False,
            }
        )

    return items


def resolve_gateway_for_method(method: str, gateway_name: str = "") -> PaymentGatewayConfig | None:
    """Resolve the configured gateway for a payment method."""

    settings = load_payment_settings()
    candidates = settings.list_available_gateways(method=method)
    if gateway_name:
        for item in candidates:
            if item.name == gateway_name:
                return item
    return candidates[0] if candidates else None


def build_payment_action(
    *,
    order: BookingOrder,
    gateway: PaymentGatewayConfig | None,
    payment_no: str,
) -> dict[str, Any]:
    """Build the frontend action payload for the selected gateway."""

    if gateway is None:
        return {
            "type": "mock_success",
            "status": "paid",
            "title": "模拟支付已完成",
            "message": "当前订单已按模拟支付流程完成。",
            "redirect_url": f"/payment/result/{order.id}",
            "instructions": [
                "这是演示支付链路，系统会直接更新订单为已支付。",
                "可在管理端支付网关中关闭模拟支付入口。",
            ],
            "client_payload": {
                "order_id": order.id,
                "payment_no": payment_no,
                "payment_method": "mock",
            },
        }

    scene_label = PAYMENT_SCENE_LABELS.get(gateway.primary_scene, gateway.primary_scene or "支付")
    action_type = "redirect_url" if gateway.checkout_url else "sdk_parameters"
    redirect_url = gateway.checkout_url or gateway.return_url or ""
    instructions = [
        f"支付网关：{gateway.label}",
        f"主支付场景：{scene_label}",
        "当前返回的是统一支付动作协议，前端可直接消费这些参数接入真实支付 SDK 或收银台。",
    ]
    if not gateway.checkout_url:
        instructions.append("该网关未配置托管收银台地址，因此本次支付会进入“待完成接入/待回调确认”状态。")

    return {
        "type": action_type,
        "status": "pending",
        "title": "支付请求已创建",
        "message": f"已为订单 {order.order_no} 创建 {gateway.label} 支付请求，请继续完成支付。",
        "redirect_url": redirect_url,
        "instructions": instructions,
        "client_payload": {
            "gateway_name": gateway.name,
            "gateway_label": gateway.label,
            "provider_type": gateway.provider_type,
            "payment_method": gateway.payment_method,
            "scene": gateway.primary_scene,
            "sandbox": gateway.sandbox,
            "payment_no": payment_no,
            "order_no": order.order_no,
            "order_id": order.id,
            "amount": str(order.pay_amount),
            "currency": "CNY",
            "gateway_url": gateway.gateway_url,
            "notify_url": gateway.notify_url,
            "return_url": gateway.return_url,
            "checkout_url": gateway.checkout_url,
            "app_id": gateway.app_id,
            "merchant_id": gateway.merchant_id,
            "merchant_name": gateway.merchant_name,
            "merchant_cert_serial_no": gateway.merchant_cert_serial_no,
            "sign_type": gateway.sign_type,
            "charset": gateway.charset,
            "scenes": gateway.normalized_scenes,
            "extra": gateway.extra or {},
        },
    }
