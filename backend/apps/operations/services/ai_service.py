"""apps/operations/services/ai_service.py —— AI 对话服务封装（多模型支持）。"""

from __future__ import annotations

import logging
from typing import Any

from config.ai import build_ai_client, load_ai_settings, AIProviderConfig

logger = logging.getLogger(__name__)


class AIChatService:
    """AI 对话服务封装，支持多供应商切换与可用性判断。"""

    def __init__(self, provider_name: str | None = None) -> None:
        """
        加载 AI 配置。

        Args:
            provider_name: 指定供应商名称；为 None 时使用当前活跃供应商。
        """
        self.settings = load_ai_settings()
        if provider_name:
            self._provider = self.settings.get_provider(provider_name)
        else:
            self._provider = self.settings.get_active_provider()

    @property
    def provider(self) -> AIProviderConfig | None:
        """当前使用的供应商配置。"""
        return self._provider

    def is_available(self) -> bool:
        """判断当前 AI 服务是否可用（已启用且供应商密钥已配置）。"""
        return self.settings.enabled and self._provider is not None and self._provider.is_configured

    def create_chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """调用 AI 聊天补全接口并标准化返回。"""
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
