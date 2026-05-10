"""Payment gateway runtime configuration for HoteLink."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from django.apps import apps as django_apps
from django.db.utils import OperationalError, ProgrammingError


def _get_bool(name: str, default: bool = False) -> bool:
    """Read a boolean flag from environment variables."""

    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


PAYMENT_FIELD_LABELS: dict[str, str] = {
    "app_id": "应用 AppID",
    "merchant_id": "商户号",
    "merchant_name": "商户名称",
    "merchant_cert_serial_no": "商户证书序列号",
    "api_v3_key": "API v3 Key",
    "merchant_private_key": "商户私钥",
    "merchant_certificate": "商户证书",
    "platform_certificate": "微信支付平台证书",
    "platform_public_key": "微信支付平台公钥",
    "gateway_url": "网关地址",
    "checkout_url": "托管收银台地址",
    "notify_url": "异步回调地址",
    "notify_secret": "回调签名密钥",
    "return_url": "同步返回地址",
    "app_private_key": "应用私钥",
    "alipay_public_key": "支付宝公钥",
    "sign_type": "签名算法",
    "charset": "字符集",
    "scenes": "支付场景",
}

PAYMENT_SCENE_LABELS: dict[str, str] = {
    "mock": "模拟支付",
    "jsapi": "JSAPI",
    "h5": "H5 支付",
    "native": "Native 扫码",
    "page": "电脑网站支付",
    "wap": "手机网站支付",
    "app": "App 支付",
    "redirect": "跳转收银台",
}

BUILTIN_PAYMENT_TEMPLATES: dict[str, dict[str, Any]] = {
    "wechat": {
        "label": "微信支付",
        "provider_type": "wechat",
        "payment_method": "wechat",
        "description": "适合公众号、小程序、H5 和扫码支付场景。",
        "supported_scenes": ["jsapi", "h5", "native"],
        "required_fields": [
            "app_id",
            "merchant_id",
            "notify_url",
            "notify_secret",
            "api_v3_key",
            "merchant_private_key",
            "merchant_cert_serial_no",
        ],
        "default_values": {
            "gateway_url": "https://api.mch.weixin.qq.com/v3",
        },
    },
    "alipay": {
        "label": "支付宝",
        "provider_type": "alipay",
        "payment_method": "alipay",
        "description": "适合电脑网站支付、手机网站支付等场景。",
        "supported_scenes": ["page", "wap"],
        "required_fields": [
            "app_id",
            "gateway_url",
            "notify_url",
            "notify_secret",
            "app_private_key",
            "alipay_public_key",
        ],
        "default_values": {
            "gateway_url": "https://openapi.alipay.com/gateway.do",
            "sign_type": "RSA2",
            "charset": "utf-8",
        },
    },
    "custom": {
        "label": "其它支付平台",
        "provider_type": "custom",
        "payment_method": "custom",
        "description": "适合预留聚合支付、银联或企业内部支付平台接入。",
        "supported_scenes": ["redirect", "app", "h5"],
        "required_fields": ["gateway_url", "notify_url", "notify_secret"],
        "default_values": {},
    },
}

_SENSITIVE_FIELDS: dict[str, tuple[str, ...]] = {
    "wechat": (
        "notify_secret",
        "api_v3_key",
        "merchant_private_key",
        "merchant_certificate",
        "platform_certificate",
        "platform_public_key",
    ),
    "alipay": (
        "notify_secret",
        "app_private_key",
        "alipay_public_key",
    ),
    "custom": ("notify_secret",),
}


def _unique_preserve_order(values: list[str]) -> list[str]:
    """Return unique string values while keeping their original order."""

    seen: set[str] = set()
    result: list[str] = []
    for item in values:
        normalized = str(item or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


@dataclass(slots=True)
class PaymentGatewayConfig:
    """Single payment gateway runtime configuration."""

    name: str
    label: str
    provider_type: str
    payment_method: str
    enabled: bool = False
    sandbox: bool = False
    priority: int = 100
    description: str = ""
    scenes: list[str] = field(default_factory=list)
    gateway_url: str = ""
    checkout_url: str = ""
    notify_url: str = ""
    notify_secret: str = ""
    return_url: str = ""
    app_id: str = ""
    merchant_id: str = ""
    merchant_name: str = ""
    merchant_cert_serial_no: str = ""
    api_v3_key: str = ""
    merchant_private_key: str = ""
    merchant_certificate: str = ""
    platform_certificate: str = ""
    platform_public_key: str = ""
    app_private_key: str = ""
    alipay_public_key: str = ""
    sign_type: str = ""
    charset: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def template(self) -> dict[str, Any]:
        """Return template metadata for the current provider type."""

        return BUILTIN_PAYMENT_TEMPLATES.get(self.provider_type, BUILTIN_PAYMENT_TEMPLATES["custom"])

    @property
    def secret_fields(self) -> tuple[str, ...]:
        """Return secret field names for the current provider type."""

        return _SENSITIVE_FIELDS.get(self.provider_type, ())

    @property
    def supported_scenes(self) -> list[str]:
        """Return provider-supported scenes."""

        template_scenes = self.template.get("supported_scenes") or []
        return list(template_scenes)

    @property
    def normalized_scenes(self) -> list[str]:
        """Return valid scenes for the current provider."""

        allowed = set(self.supported_scenes)
        scenes = _unique_preserve_order(self.scenes)
        if not scenes:
            return list(self.supported_scenes[:1])
        return [item for item in scenes if item in allowed] or list(self.supported_scenes[:1])

    @property
    def primary_scene(self) -> str:
        """Return the first active scene used for user payment actions."""

        scenes = self.normalized_scenes
        return scenes[0] if scenes else ""

    @property
    def required_fields(self) -> list[str]:
        """Return required fields for completeness validation."""

        fields = list(self.template.get("required_fields") or [])
        if self.provider_type in {"wechat", "alipay", "custom"}:
            fields.append("scenes")
        return fields

    @property
    def missing_required_fields(self) -> list[str]:
        """Return missing field names for the current configuration."""

        missing: list[str] = []
        for field_name in self.required_fields:
            if field_name == "scenes":
                if not self.normalized_scenes:
                    missing.append(field_name)
                continue
            if not str(getattr(self, field_name, "") or "").strip():
                missing.append(field_name)
        return missing

    @property
    def missing_required_labels(self) -> list[str]:
        """Return missing field labels for UI display."""

        return [PAYMENT_FIELD_LABELS.get(name, name) for name in self.missing_required_fields]

    @property
    def is_configured(self) -> bool:
        """Return whether the gateway has enough fields for real integration."""

        return not self.missing_required_fields

    @property
    def action_type_hint(self) -> str:
        """Return the frontend action contract suggested by this gateway."""

        if self.checkout_url:
            return "redirect_url"
        return "sdk_parameters"

    def to_runtime_dict(self) -> dict[str, Any]:
        """Serialize the gateway to runtime JSON."""

        return {
            "name": self.name,
            "label": self.label,
            "provider_type": self.provider_type,
            "payment_method": self.payment_method,
            "enabled": self.enabled,
            "sandbox": self.sandbox,
            "priority": self.priority,
            "description": self.description,
            "scenes": self.normalized_scenes,
            "gateway_url": self.gateway_url,
            "checkout_url": self.checkout_url,
            "notify_url": self.notify_url,
            "notify_secret": self.notify_secret,
            "return_url": self.return_url,
            "app_id": self.app_id,
            "merchant_id": self.merchant_id,
            "merchant_name": self.merchant_name,
            "merchant_cert_serial_no": self.merchant_cert_serial_no,
            "api_v3_key": self.api_v3_key,
            "merchant_private_key": self.merchant_private_key,
            "merchant_certificate": self.merchant_certificate,
            "platform_certificate": self.platform_certificate,
            "platform_public_key": self.platform_public_key,
            "app_private_key": self.app_private_key,
            "alipay_public_key": self.alipay_public_key,
            "sign_type": self.sign_type,
            "charset": self.charset,
            "extra": self.extra or {},
        }

    def to_dict(self, *, include_secrets: bool = False) -> dict[str, Any]:
        """Serialize the gateway for API responses."""

        data = {
            "name": self.name,
            "label": self.label,
            "provider_type": self.provider_type,
            "payment_method": self.payment_method,
            "enabled": self.enabled,
            "sandbox": self.sandbox,
            "priority": self.priority,
            "description": self.description,
            "scenes": self.normalized_scenes,
            "gateway_url": self.gateway_url,
            "checkout_url": self.checkout_url,
            "notify_url": self.notify_url,
            "return_url": self.return_url,
            "app_id": self.app_id,
            "merchant_id": self.merchant_id,
            "merchant_name": self.merchant_name,
            "merchant_cert_serial_no": self.merchant_cert_serial_no,
            "sign_type": self.sign_type,
            "charset": self.charset,
            "extra": self.extra or {},
            "supported_scenes": self.supported_scenes,
            "required_fields": self.required_fields,
            "missing_required_fields": self.missing_required_fields,
            "missing_required_labels": self.missing_required_labels,
            "is_configured": self.is_configured,
            "action_type_hint": self.action_type_hint,
            "secret_flags": {field_name: bool(str(getattr(self, field_name, "") or "").strip()) for field_name in self.secret_fields},
        }
        if include_secrets:
            for field_name in self.secret_fields:
                data[field_name] = getattr(self, field_name, "")
        return data


@dataclass(slots=True)
class PaymentSettings:
    """Collection of runtime payment settings."""

    mock_enabled: bool = True
    gateways: dict[str, PaymentGatewayConfig] = field(default_factory=dict)

    def get_gateway(self, name: str) -> PaymentGatewayConfig | None:
        """Return a gateway by name."""

        return self.gateways.get(name)

    def list_gateways(self, *, include_secrets: bool = False) -> list[dict[str, Any]]:
        """Return serialized gateways sorted by priority."""

        ordered = sorted(
            self.gateways.values(),
            key=lambda item: (item.priority, item.label or item.name, item.name),
        )
        return [item.to_dict(include_secrets=include_secrets) for item in ordered]

    def list_available_gateways(self, *, method: str | None = None) -> list[PaymentGatewayConfig]:
        """Return gateways that are enabled and configured for user payments."""

        gateways = [
            item
            for item in self.gateways.values()
            if item.enabled and item.is_configured and (method is None or item.payment_method == method)
        ]
        return sorted(gateways, key=lambda item: (item.priority, item.label or item.name, item.name))


_RUNTIME_CONFIG_PATH: Path | None = None
_RUNTIME_CONFIG_KEY = "payment_runtime"
_SETTINGS_CACHE_KEY = "config.payment_settings"
_SETTINGS_CACHE_TTL = 60


def _get_runtime_config_path() -> Path:
    """Return the on-disk runtime config path."""

    global _RUNTIME_CONFIG_PATH
    if _RUNTIME_CONFIG_PATH is None:
        base_dir = Path(__file__).resolve().parent.parent
        _RUNTIME_CONFIG_PATH = base_dir / ".payment_gateways.json"
    return _RUNTIME_CONFIG_PATH


def _load_runtime_config() -> dict[str, Any]:
    """Load runtime config from database or fallback file."""

    try:
        if django_apps.ready:
            runtime_model = django_apps.get_model("operations", "RuntimeConfig")
            row = runtime_model.objects.filter(key=_RUNTIME_CONFIG_KEY).values_list("value", flat=True).first()
            if isinstance(row, dict):
                return row
    except (LookupError, OperationalError, ProgrammingError):
        pass
    except Exception:
        pass

    path = _get_runtime_config_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def _save_runtime_config(data: dict[str, Any]) -> None:
    """Persist runtime config to database and fallback file."""

    persisted = False
    try:
        if django_apps.ready:
            runtime_model = django_apps.get_model("operations", "RuntimeConfig")
            runtime_model.objects.update_or_create(
                key=_RUNTIME_CONFIG_KEY,
                defaults={"value": data},
            )
            persisted = True
    except (LookupError, OperationalError, ProgrammingError):
        pass
    except Exception:
        pass

    path = _get_runtime_config_path()
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        persisted = True
    except OSError:
        if not persisted:
            raise


def _sanitize_name(value: str) -> str:
    """Normalize gateway identifiers."""

    normalized = "".join(char for char in str(value or "").strip().lower() if char.isalnum() or char in {"_", "-"})
    return normalized


def _gateway_from_dict(data: dict[str, Any]) -> PaymentGatewayConfig | None:
    """Build a gateway config from runtime JSON."""

    provider_type = str(data.get("provider_type") or "custom").strip() or "custom"
    template = BUILTIN_PAYMENT_TEMPLATES.get(provider_type, BUILTIN_PAYMENT_TEMPLATES["custom"])
    defaults = template.get("default_values") or {}
    name = _sanitize_name(str(data.get("name") or ""))
    if not name:
        return None
    label = str(data.get("label") or template.get("label") or name).strip() or name
    payment_method = str(data.get("payment_method") or template.get("payment_method") or "custom").strip() or "custom"
    raw_scenes = data.get("scenes") or template.get("supported_scenes") or []
    if not isinstance(raw_scenes, list):
        raw_scenes = [raw_scenes]
    return PaymentGatewayConfig(
        name=name,
        label=label,
        provider_type=provider_type,
        payment_method=payment_method,
        enabled=bool(data.get("enabled", False)),
        sandbox=bool(data.get("sandbox", False)),
        priority=int(data.get("priority", 100) or 100),
        description=str(data.get("description") or template.get("description") or "").strip(),
        scenes=[str(item) for item in raw_scenes],
        gateway_url=str(data.get("gateway_url") or defaults.get("gateway_url") or "").strip(),
        checkout_url=str(data.get("checkout_url") or "").strip(),
        notify_url=str(data.get("notify_url") or "").strip(),
        notify_secret=str(data.get("notify_secret") or "").strip(),
        return_url=str(data.get("return_url") or "").strip(),
        app_id=str(data.get("app_id") or "").strip(),
        merchant_id=str(data.get("merchant_id") or "").strip(),
        merchant_name=str(data.get("merchant_name") or "").strip(),
        merchant_cert_serial_no=str(data.get("merchant_cert_serial_no") or "").strip(),
        api_v3_key=str(data.get("api_v3_key") or "").strip(),
        merchant_private_key=str(data.get("merchant_private_key") or "").strip(),
        merchant_certificate=str(data.get("merchant_certificate") or "").strip(),
        platform_certificate=str(data.get("platform_certificate") or "").strip(),
        platform_public_key=str(data.get("platform_public_key") or "").strip(),
        app_private_key=str(data.get("app_private_key") or "").strip(),
        alipay_public_key=str(data.get("alipay_public_key") or "").strip(),
        sign_type=str(data.get("sign_type") or defaults.get("sign_type") or "").strip(),
        charset=str(data.get("charset") or defaults.get("charset") or "").strip(),
        extra=data.get("extra") if isinstance(data.get("extra"), dict) else {},
    )


def load_payment_settings() -> PaymentSettings:
    """Load payment settings from cache, runtime config, and environment defaults."""

    from django.core.cache import cache

    cached = cache.get(_SETTINGS_CACHE_KEY)
    if isinstance(cached, PaymentSettings):
        return cached

    runtime = _load_runtime_config()
    mock_enabled = bool(runtime.get("mock_enabled", _get_bool("PAYMENT_MOCK_ENABLED", True)))
    gateways: dict[str, PaymentGatewayConfig] = {}
    for raw_gateway in runtime.get("gateways", []):
        if not isinstance(raw_gateway, dict):
            continue
        gateway = _gateway_from_dict(raw_gateway)
        if gateway is None:
            continue
        gateways[gateway.name] = gateway

    result = PaymentSettings(mock_enabled=mock_enabled, gateways=gateways)
    cache.set(_SETTINGS_CACHE_KEY, result, _SETTINGS_CACHE_TTL)
    return result


def update_payment_settings(*, mock_enabled: bool | None = None) -> PaymentSettings:
    """Update runtime payment settings and return the latest view."""

    runtime = _load_runtime_config()
    if mock_enabled is not None:
        runtime["mock_enabled"] = bool(mock_enabled)
    _save_runtime_config(runtime)

    from django.core.cache import cache

    cache.delete(_SETTINGS_CACHE_KEY)
    return load_payment_settings()


def save_payment_gateway(data: dict[str, Any]) -> PaymentSettings:
    """Create or update a payment gateway and return the latest settings."""

    runtime = _load_runtime_config()
    existing_gateways = {
        item.get("name"): item
        for item in runtime.get("gateways", [])
        if isinstance(item, dict) and item.get("name")
    }

    gateway = _gateway_from_dict(data)
    if gateway is None:
        raise ValueError("gateway name is required")

    current = dict(existing_gateways.get(gateway.name) or {})
    payload = gateway.to_runtime_dict()

    # Preserve secrets when the edit form intentionally leaves them blank.
    for secret_field in gateway.secret_fields:
        if not payload.get(secret_field) and current.get(secret_field):
            payload[secret_field] = current.get(secret_field)

    existing_gateways[gateway.name] = payload
    runtime["gateways"] = list(existing_gateways.values())
    _save_runtime_config(runtime)

    from django.core.cache import cache

    cache.delete(_SETTINGS_CACHE_KEY)
    return load_payment_settings()


def delete_payment_gateway(name: str) -> PaymentSettings:
    """Delete a runtime payment gateway and return the latest settings."""

    runtime = _load_runtime_config()
    normalized = _sanitize_name(name)
    runtime["gateways"] = [
        item
        for item in runtime.get("gateways", [])
        if isinstance(item, dict) and _sanitize_name(item.get("name")) != normalized
    ]
    _save_runtime_config(runtime)

    from django.core.cache import cache

    cache.delete(_SETTINGS_CACHE_KEY)
    return load_payment_settings()


def list_builtin_payment_templates() -> list[dict[str, Any]]:
    """Return builtin payment gateway templates for the admin UI."""

    result: list[dict[str, Any]] = []
    for name, template in BUILTIN_PAYMENT_TEMPLATES.items():
        result.append(
            {
                "name": name,
                "label": template.get("label") or name,
                "provider_type": template.get("provider_type") or name,
                "payment_method": template.get("payment_method") or "custom",
                "description": template.get("description") or "",
                "supported_scenes": list(template.get("supported_scenes") or []),
                "required_fields": list(template.get("required_fields") or []),
                "default_values": dict(template.get("default_values") or {}),
            }
        )
    return result
