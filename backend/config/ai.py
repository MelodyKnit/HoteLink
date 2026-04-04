from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class AISettings:
    provider: str
    enabled: bool
    base_url: str
    api_key: str
    chat_model: str
    reasoning_model: str
    timeout: float

    @property
    def is_configured(self) -> bool:
        return self.enabled and bool(self.api_key)


def load_ai_settings() -> AISettings:
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
    ai_settings = settings or load_ai_settings()
    if not ai_settings.api_key:
        raise ValueError("AI_API_KEY is not configured.")
    return OpenAI(
        api_key=ai_settings.api_key,
        base_url=ai_settings.base_url,
        timeout=ai_settings.timeout,
    )
