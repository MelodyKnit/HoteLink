"""apps/operations/services/prompt_service.py —— Jinja 提示词模板加载与场景约束。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.conf import settings
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

SUPPORTED_SCENE_ALIASES = {
    "general": "customer_service",
    "customer_service": "customer_service",
    "booking_assistant": "customer_service",
}

# 管理端 AI 场景（不需要别名映射，直接支持）
ADMIN_AI_SCENES = {
    "report_summary",
    "review_summary",
    "reply_suggestion",
    "pricing_suggestion",
    "business_report",
    "marketing_copy",
    "content_generate",
    "review_sentiment",
    "anomaly_report",
}

# 用户端 AI 场景
USER_AI_SCENES = {
    "recommendations",
    "hotel_compare",
}

SUPPORTED_CUSTOMER_SERVICE_TOPICS = (
    "酒店基础信息",
    "房型基础信息",
    "用户本人订单状态",
    "用户评价与回复",
    "支付与发票流程",
    "系统通知",
)


class PromptSceneError(ValueError):
    """提示词场景非法或模板缺失。"""


class PromptTemplateService:
    """统一管理后端 prompts 目录下的 Jinja 模板。"""

    def __init__(self) -> None:
        prompts_dir = Path(settings.BASE_DIR) / "prompts"
        self.env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def normalize_scene(self, scene: str) -> str:
        normalized_scene = SUPPORTED_SCENE_ALIASES.get(scene, scene)
        if normalized_scene != "customer_service":
            raise PromptSceneError(f"unsupported AI scene: {scene}")
        return normalized_scene

    def render(self, template_name: str, **context: Any) -> str:
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound as exc:
            raise PromptSceneError(f"prompt template not found: {template_name}") from exc
        return template.render(**context).strip()

    def render_admin(self, scene: str, template_type: str, **context: Any) -> str:
        """渲染管理端或用户端 AI 场景模板。

        Args:
            scene: 场景名称（如 report_summary / review_sentiment 等）
            template_type: "system" 或 "user"
            **context: 模板变量
        """
        allowed = ADMIN_AI_SCENES | USER_AI_SCENES
        if scene not in allowed:
            raise PromptSceneError(f"unsupported admin AI scene: {scene}")
        template_name = f"{scene}/{template_type}.j2"
        return self.render(template_name, **context)

    def dumps(self, payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2, default=str)