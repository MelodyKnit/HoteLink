"""apps/operations/services/ai_service.py —— AI 对话服务封装。"""

from __future__ import annotations

from typing import Any

from config.ai import build_ai_client, load_ai_settings


class AIChatService:
    """AI 对话服务封装，统一可用性判断与调用返回结构。"""

    def __init__(self) -> None:
        """加载 AI 配置并缓存到服务实例。"""
        self.settings = load_ai_settings()

    def is_available(self) -> bool:
        """判断当前 AI 服务是否可用（已启用且密钥已配置）。"""
        return self.settings.is_configured

    def create_chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """调用 AI 聊天补全接口并标准化返回。"""
        if not self.is_available():
            raise RuntimeError("AI service is not configured. Check AI_ENABLED and AI_API_KEY.")

        client = build_ai_client(self.settings)
        response = client.chat.completions.create(
            model=model or self.settings.chat_model,
            messages=messages,
            temperature=temperature,
        )
        content = ""
        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content or ""

        return {
            "model": response.model,
            "content": content,
            "raw": response.model_dump(),
        }
