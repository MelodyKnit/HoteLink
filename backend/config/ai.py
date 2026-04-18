"""
config/ai.py —— AI 服务配置与客户端工厂（多模型支持）。

职责：
  - 定义 AIProviderConfig 数据类，描述单个 AI 供应商的配置；
  - 定义 AISettings 数据类，管理多个供应商和当前活跃供应商选择；
  - 提供 load_ai_settings() 从环境变量读取配置（支持多供应商）；
  - 提供 build_ai_client() 工厂函数，基于指定供应商构造 OpenAI 兼容客户端；
  - 支持运行时通过 update_ai_settings() 动态切换活跃供应商。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from django.apps import apps as django_apps
from django.db.utils import OperationalError, ProgrammingError

from openai import OpenAI


def _get_bool(name: str, default: bool = False) -> bool:
    """从环境变量读取布尔值，支持 '1'/'true'/'yes'/'on' 等字符串形式。"""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# 内置供应商预设：provider_name -> (base_url, default_chat_model, default_reasoning_model)
BUILTIN_PROVIDERS: dict[str, dict[str, str]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "chat_model": "deepseek-chat",
        "reasoning_model": "deepseek-reasoner",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "chat_model": "gpt-4o-mini",
        "reasoning_model": "gpt-4o",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "chat_model": "glm-4-flash",
        "reasoning_model": "glm-4",
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "chat_model": "moonshot-v1-8k",
        "reasoning_model": "moonshot-v1-32k",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "chat_model": "qwen-turbo",
        "reasoning_model": "qwen-plus",
    },
}


@dataclass(slots=True)
class AIProviderConfig:
    """单个 AI 供应商配置。"""

    name: str              # 供应商标识，如 deepseek / openai / zhipu
    label: str             # 供应商显示名称
    base_url: str          # API 基础 URL
    api_key: str           # API 密钥
    chat_model: str        # 通用对话模型名称
    reasoning_model: str   # 推理/思维链模型名称
    timeout: float = 60    # 请求超时时间（秒）

    @property
    def is_configured(self) -> bool:
        """当 API 密钥不为空时，返回 True。"""
        return bool(self.api_key)

    def to_dict(self, *, include_api_key: bool = False) -> dict[str, Any]:
        """序列化为字典，默认隐藏完整 api_key。"""
        data = {
            "name": self.name,
            "label": self.label,
            "base_url": self.base_url,
            "api_key_configured": self.is_configured,
            "chat_model": self.chat_model,
            "reasoning_model": self.reasoning_model,
            "timeout": self.timeout,
        }
        if include_api_key:
            data["api_key"] = self.api_key
        return data


@dataclass(slots=True)
class AISettings:
    """AI 服务参数集合，支持多供应商配置和活跃供应商切换。"""

    enabled: bool                                       # 是否启用 AI 功能
    active_provider: str                                # 当前活跃供应商名称
    providers: dict[str, AIProviderConfig] = field(default_factory=dict)  # 所有已配置供应商

    @property
    def is_configured(self) -> bool:
        """当 AI 功能已启用且当前活跃供应商密钥已配置时，返回 True。"""
        provider = self.providers.get(self.active_provider)
        return self.enabled and provider is not None and provider.is_configured

    def get_active_provider(self) -> AIProviderConfig | None:
        """获取当前活跃供应商配置，不存在则返回 None。"""
        return self.providers.get(self.active_provider)

    def get_provider(self, name: str) -> AIProviderConfig | None:
        """按名称获取指定供应商配置。"""
        return self.providers.get(name)

    def list_providers(self, *, include_api_key: bool = False) -> list[dict[str, Any]]:
        """返回所有供应商的摘要信息列表。"""
        result = []
        for p in self.providers.values():
            info = p.to_dict(include_api_key=include_api_key)
            info["is_active"] = p.name == self.active_provider
            result.append(info)
        return result


# ---------- 运行时配置持久化路径 ----------
_RUNTIME_CONFIG_PATH: Path | None = None
_RUNTIME_CONFIG_KEY = "ai_runtime"


def _get_runtime_config_path() -> Path:
    """获取运行时 AI 配置持久化文件路径。"""
    global _RUNTIME_CONFIG_PATH
    if _RUNTIME_CONFIG_PATH is None:
        base_dir = Path(__file__).resolve().parent.parent
        _RUNTIME_CONFIG_PATH = base_dir / ".ai_providers.json"
    return _RUNTIME_CONFIG_PATH


def _load_runtime_config() -> dict[str, Any]:
    """从本地磁盘加载运行时 AI 配置。"""
    # 优先使用数据库持久化，确保容器重启/镜像更新后不丢失。
    try:
        if django_apps.ready:
            RuntimeConfig = django_apps.get_model("operations", "RuntimeConfig")
            row = RuntimeConfig.objects.filter(key=_RUNTIME_CONFIG_KEY).values_list("value", flat=True).first()
            if isinstance(row, dict):
                return row
    except (LookupError, OperationalError, ProgrammingError):
        pass
    except Exception:
        pass

    # 兼容历史文件存储（作为兜底）。
    path = _get_runtime_config_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_runtime_config(data: dict[str, Any]) -> None:
    """将运行时 AI 配置持久化到本地磁盘。"""
    # 优先保存到数据库，保证重启后可恢复。
    persisted = False
    try:
        if django_apps.ready:
            RuntimeConfig = django_apps.get_model("operations", "RuntimeConfig")
            RuntimeConfig.objects.update_or_create(
                key=_RUNTIME_CONFIG_KEY,
                defaults={"value": data},
            )
            persisted = True
    except (LookupError, OperationalError, ProgrammingError):
        pass
    except Exception:
        pass

    # 同步保存到历史文件，便于兼容和排查。
    path = _get_runtime_config_path()
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        persisted = True
    except OSError:
        if not persisted:
            raise


_AI_SETTINGS_CACHE_KEY = "config.ai_settings"
_AI_SETTINGS_CACHE_TTL = 60  # seconds


def load_ai_settings() -> AISettings:
    """
    从环境变量和运行时配置加载 AI 设置。

    加载优先级：运行时配置 > 环境变量 > 内置默认值。
    环境变量定义主供应商（向后兼容），运行时配置可添加额外供应商。
    """
    from django.core.cache import cache

    cached = cache.get(_AI_SETTINGS_CACHE_KEY)
    if isinstance(cached, AISettings):
        return cached

    enabled = _get_bool("AI_ENABLED", False)

    # 从环境变量构建主供应商（向后兼容）
    env_provider_name = os.getenv("AI_PROVIDER", "deepseek")
    builtin = BUILTIN_PROVIDERS.get(env_provider_name, BUILTIN_PROVIDERS["deepseek"])
    primary = AIProviderConfig(
        name=env_provider_name,
        label=env_provider_name.capitalize(),
        base_url=os.getenv("AI_BASE_URL", builtin["base_url"]),
        api_key=os.getenv("AI_API_KEY", ""),
        chat_model=os.getenv("AI_MODEL", builtin["chat_model"]),
        reasoning_model=os.getenv("AI_REASONING_MODEL", builtin["reasoning_model"]),
        timeout=float(os.getenv("AI_TIMEOUT", "60")),
    )

    providers: dict[str, AIProviderConfig] = {primary.name: primary}
    active_provider = env_provider_name

    # 加载运行时配置（额外供应商 + 活跃供应商选择）
    runtime = _load_runtime_config()
    if runtime.get("enabled") is not None:
        enabled = bool(runtime["enabled"])
    if runtime.get("active_provider"):
        active_provider = runtime["active_provider"]

    for p_data in runtime.get("providers", []):
        name = p_data.get("name", "")
        if not name:
            continue
        providers[name] = AIProviderConfig(
            name=name,
            label=p_data.get("label", name.capitalize()),
            base_url=p_data.get("base_url", ""),
            api_key=p_data.get("api_key", ""),
            chat_model=p_data.get("chat_model", ""),
            reasoning_model=p_data.get("reasoning_model", ""),
            timeout=float(p_data.get("timeout", 60)),
        )

    # 确保 active_provider 有效
    if active_provider not in providers:
        active_provider = primary.name

    result = AISettings(enabled=enabled, active_provider=active_provider, providers=providers)
    cache.set(_AI_SETTINGS_CACHE_KEY, result, _AI_SETTINGS_CACHE_TTL)
    return result


def update_ai_settings(
    *,
    enabled: bool | None = None,
    active_provider: str | None = None,
    provider_configs: list[dict[str, Any]] | None = None,
) -> AISettings:
    """
    更新运行时 AI 配置并持久化到磁盘，然后返回最新设置。

    Args:
        enabled: 是否启用 AI 功能。
        active_provider: 切换活跃供应商名称。
        provider_configs: 更新供应商配置列表（增量合并）。
    """
    runtime = _load_runtime_config()

    if enabled is not None:
        runtime["enabled"] = enabled
    if active_provider is not None:
        runtime["active_provider"] = active_provider

    if provider_configs is not None:
        existing = {p["name"]: p for p in runtime.get("providers", [])}
        for pc in provider_configs:
            name = pc.get("name", "")
            if not name:
                continue
            if name in existing:
                existing[name].update(pc)
            else:
                existing[name] = pc
        runtime["providers"] = list(existing.values())

    _save_runtime_config(runtime)
    from django.core.cache import cache
    cache.delete(_AI_SETTINGS_CACHE_KEY)
    return load_ai_settings()


def delete_ai_provider(provider_name: str) -> AISettings:
    """删除指定名称的运行时 AI 供应商配置并返回最新设置。"""
    runtime = _load_runtime_config()
    runtime["providers"] = [p for p in runtime.get("providers", []) if p.get("name") != provider_name]
    _save_runtime_config(runtime)
    from django.core.cache import cache
    cache.delete(_AI_SETTINGS_CACHE_KEY)
    return load_ai_settings()


def build_ai_client(provider: AIProviderConfig | None = None) -> OpenAI:
    """
    构造 OpenAI 兼容的 API 客户端。

    Args:
        provider: 可选的 AIProviderConfig 实例；为 None 时使用当前活跃供应商。

    Returns:
        配置好 base_url / api_key / timeout 的 OpenAI 客户端实例。

    Raises:
        ValueError: 当 API 密钥未配置时抛出。
    """
    if provider is None:
        settings = load_ai_settings()
        provider = settings.get_active_provider()
        if provider is None:
            raise ValueError("No active AI provider configured.")
    if not provider.api_key:
        raise ValueError(f"API key is not configured for provider '{provider.name}'.")
    return OpenAI(
        api_key=provider.api_key,
        base_url=provider.base_url,
        timeout=provider.timeout,
    )
