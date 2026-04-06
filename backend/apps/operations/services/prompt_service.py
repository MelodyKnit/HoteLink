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

SUPPORTED_CUSTOMER_SERVICE_TOPICS = (
    "酒店基础信息",
    "房型基础信息",
    "用户本人订单状态",
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

    def dumps(self, payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2, default=str)