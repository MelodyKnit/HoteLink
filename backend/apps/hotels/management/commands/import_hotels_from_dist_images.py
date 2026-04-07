from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


def candidate_paths() -> list[Path]:
    env_dir = os.getenv("HOTELINK_LOCAL_SEED_DIR", "").strip()
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir) / "import_hotels_from_dist_images.py")
    candidates.append(Path(settings.BASE_DIR) / "private" / "local-dev" / "seed_commands" / "import_hotels_from_dist_images.py")
    candidates.append(Path(settings.BASE_DIR).parent / "private" / "local-dev" / "seed_commands" / "import_hotels_from_dist_images.py")
    return candidates


def resolve_local_impl_path() -> Path | None:
    for path in candidate_paths():
        if path.exists():
            return path
    return None


def load_local_module(path: Path):
    spec = spec_from_file_location("local_import_hotels_from_dist_images", path)
    if not spec or not spec.loader:
        raise CommandError(f"无法加载本地脚本: {path}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Command(BaseCommand):
    help = "导入酒店伪数据（逻辑位于 private/local-dev/seed_commands）"

    def add_arguments(self, parser):
        local_path = resolve_local_impl_path()
        if not local_path:
            return
        module = load_local_module(local_path)
        add_arguments = getattr(module, "add_arguments", None)
        if callable(add_arguments):
            add_arguments(parser)

    def handle(self, *args, **options):
        local_path = resolve_local_impl_path()
        if not local_path:
            raise CommandError(
                "未找到本地伪数据脚本，请在 backend/private/local-dev/seed_commands/import_hotels_from_dist_images.py 或 private/local-dev/seed_commands/import_hotels_from_dist_images.py 中实现 run(command, *args, **options)"
            )
        module = load_local_module(local_path)
        run = getattr(module, "run", None)
        if not callable(run):
            raise CommandError("本地伪数据脚本缺少可调用函数 run(command, *args, **options)")
        return run(self, *args, **options)