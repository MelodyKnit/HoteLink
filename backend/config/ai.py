"""
config/ai.py —— AI 服务配置与客户端工厂。

职责：
  - 定义 AISettings 数据类，统一封装所有 AI 相关环境变量；
  - 提供 load_ai_settings() 从环境变量读取配置；
  - 提供 build_ai_client() 工厂函数，基于当前配置构造 OpenAI 兼容客户端
    （默认对接 DeepSeek API）。
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI


def _get_bool(name: str, default: bool = False) -> bool:
    """从环境变量读取布尔值，支持 '1'/'true'/'yes'/'on' 等字符串形式。"""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class AISettings:
    """AI 服务参数集合，由环境变量填充，在整个项目中作单例使用。"""

    provider: str          # AI 提供商名称，默认 deepseek
    enabled: bool          # 是否启用 AI 功能
    base_url: str          # API 基础 URL
    api_key: str           # API 密钥
    chat_model: str        # 通用对话模型名称
    reasoning_model: str   # 推理/思维链模型名称
    timeout: float         # 请求超时时间（秒）

    @property
    def is_configured(self) -> bool:
        """当 AI 功能已启用且 API 密钥不为空时，返回 True。"""
        return self.enabled and bool(self.api_key)


def load_ai_settings() -> AISettings:
    """从环境变量加载 AI 配置，返回 AISettings 实例。"""
    return AISettings(
        provider=os.getenv("AI_PROVIDER", "deepseek"),
        enabled=_get_bool("AI_ENABLED", False),
        base_url=os.getenv("AI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.getenv("AI_API_KEY", ""),
        chat_model=os.getenv("AI_MODEL", "deepseek-chat"),
        reasoning_model=os.getenv("AI_REASONING_MODEL", "deepseek-reasoner"),
        timeout=float(os.getenv("AI_TIMEOUT", "60")),
    )


def build_ai_client(settings: AISettings | None = None) -> OpenAI:
    """
    构造 OpenAI 兼容的 API 客户端。

    Args:
        settings: 可选的 AISettings 实例；为 None 时自动从环境变量加载。

    Returns:
        配置好 base_url / api_key / timeout 的 OpenAI 客户端实例。

    Raises:
        ValueError: 当 API 密钥未配置时抛出。
    """
    ai_settings = settings or load_ai_settings()
    if not ai_settings.api_key:
        raise ValueError("AI_API_KEY is not configured.")
    return OpenAI(
        api_key=ai_settings.api_key,
        base_url=ai_settings.base_url,
        timeout=ai_settings.timeout,
    )
