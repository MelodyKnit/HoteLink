from __future__ import annotations

import argparse
import ast
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


HTTP_METHOD_NAMES = {"get", "post", "put", "patch", "delete", "head", "options"}


@dataclass(frozen=True)
class RouteItem:
    method: str
    path: str
    view: str
    name: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_view_methods(views_py: Path) -> dict[str, list[str]]:
    tree = ast.parse(read_text(views_py))
    classes: dict[str, dict[str, set[str] | list[str]]] = {}

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        own = {
            item.name.upper()
            for item in node.body
            if isinstance(item, ast.FunctionDef) and item.name in HTTP_METHOD_NAMES
        }
        bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
        classes[node.name] = {"own": own, "bases": bases}

    resolved: dict[str, set[str]] = {}

    def resolve_methods(class_name: str, stack: set[str] | None = None) -> set[str]:
        if class_name in resolved:
            return resolved[class_name]
        if class_name not in classes:
            return set()
        if stack is None:
            stack = set()
        if class_name in stack:
            return set()

        stack.add(class_name)
        methods = set(classes[class_name]["own"])  # type: ignore[arg-type]
        for base_name in classes[class_name]["bases"]:  # type: ignore[index]
            methods |= resolve_methods(base_name, stack)

        resolved[class_name] = methods
        return methods

    for class_name in classes:
        resolve_methods(class_name)

    output: dict[str, list[str]] = {}
    for class_name, methods in resolved.items():
        if not methods:
            methods = {"GET"}
        output[class_name] = sorted(methods)
    return output


def parse_routes(urls_py: Path, view_methods: dict[str, list[str]]) -> list[RouteItem]:
    source = read_text(urls_py)
    pattern = re.compile(
        r'path\(\s*"([^"]*)"\s*,\s*([A-Za-z0-9_]+)\.as_view\(\)\s*,\s*name="([^"]+)"\s*\)'
    )

    items: list[RouteItem] = []
    for path_str, view_name, route_name in pattern.findall(source):
        methods = view_methods.get(view_name, ["GET"])
        items.append(
            RouteItem(
                method=",".join(methods),
                path=f"/api/v1/{path_str}",
                view=view_name,
                name=route_name,
            )
        )
    return items


def bucket_key(path: str) -> str:
    if path == "/api/v1/":
        return "root"
    for prefix in ("system", "common", "public", "user", "admin"):
        if path.startswith(f"/api/v1/{prefix}/"):
            return prefix
    return "other"


def render_markdown(routes: Iterable[RouteItem]) -> str:
    route_list = sorted(routes, key=lambda item: item.path)
    buckets: dict[str, list[RouteItem]] = defaultdict(list)
    for item in route_list:
        buckets[bucket_key(item.path)].append(item)

    order = ["root", "system", "common", "public", "user", "admin", "other"]
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = [
        "# HoteLink API 路由清单（源码自动生成）",
        "",
        f"- 生成时间：{generated_at}",
        "- 来源文件：`backend/apps/api/urls.py` + `backend/apps/api/views.py`",
        f"- 总路由数：**{len(route_list)}**",
        "",
        "> 本文件由 `scripts/docs/generate_api_inventory.py` 生成，请勿手工编辑。",
        "",
    ]

    for key in order:
        items = buckets.get(key)
        if not items:
            continue
        title = {
            "root": "Root",
            "system": "System",
            "common": "Common",
            "public": "Public",
            "user": "User",
            "admin": "Admin",
            "other": "Other",
        }[key]
        lines.extend(
            [
                f"## {title}",
                "",
                "| Method | Path | View | Name |",
                "|---|---|---|---|",
            ]
        )
        for item in items:
            lines.append(
                f"| `{item.method}` | `{item.path}` | `{item.view}` | `{item.name}` |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate docs/api-inventory.md from backend route source."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path (default: current directory)",
    )
    parser.add_argument(
        "--output",
        default="docs/api-inventory.md",
        help="Output markdown path (default: docs/api-inventory.md)",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    urls_py = repo_root / "backend" / "apps" / "api" / "urls.py"
    views_py = repo_root / "backend" / "apps" / "api" / "views.py"
    output_md = repo_root / args.output

    view_methods = parse_view_methods(views_py)
    routes = parse_routes(urls_py, view_methods)
    markdown = render_markdown(routes)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(markdown, encoding="utf-8")
    print(f"Generated {output_md} ({len(routes)} routes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
